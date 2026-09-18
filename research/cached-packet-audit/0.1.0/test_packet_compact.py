"""Independent tiny wire fixtures for the bounded footer operation."""
import struct
import unittest

from compact_footer import (Cursor, TRUE, FALSE, BYTE, I16, I32, I64, DOUBLE,
                            BINARY, LIST, SET, MAP, STRUCT, list_header,
                            remove_arrow_schema, varint)


def binary(value):return varint(len(value))+value


def item(key,value=b'value',extra=b''):
    return b'\x18'+binary(key)+(b'' if value is None else b'\x18'+binary(value))+extra+b'\x00'


def footer(items):
    # Field 1/version; field 5/key-value list; field 6/creator; stop.
    return b'\x15\x02\x49'+list_header(len(items),STRUCT)+b''.join(items)+b'\x18\x07creator\x00'


class CompactControls(unittest.TestCase):
    def test_spec_varint_and_collection_boundaries(self):
        self.assertEqual(varint(50399),b'\xdf\x89\x03')
        for value in (0,1,127,128,16383,16384,2**64-1):
            self.assertEqual(Cursor(varint(value)).uint(),value)
        for size in (0,1,14,15,16,127,128,1000000):
            self.assertEqual(Cursor(list_header(size,STRUCT)).list(),(size,STRUCT))
        self.assertEqual(list_header(14,STRUCT),b'\xec')
        self.assertEqual(list_header(15,STRUCT),b'\xfc\x0f')

    def test_removal_preserves_every_surviving_item_and_field(self):
        for count in (1,2,14,15,16,128):
            for position in sorted({0,count//2,count-1}):
                items=[item(('key-%d'%i).encode()) for i in range(count)]
                items[position]=item(b'ARROW:schema',b'opaque-serialized-schema')
                source=footer(items);result,record=remove_arrow_schema(source)
                self.assertEqual(result,footer(items[:position]+items[position+1:]))
                self.assertTrue(record['all_surviving_footer_field_bytes_preserved'])
        self.assertEqual(remove_arrow_schema(footer([item(b'ARROW:schema')]))[0],footer([]))

    def test_unknown_fields_and_all_supported_container_types_survive(self):
        # Unknown KeyValue fields 3..12; booleans in fields carry no extra byte.
        extra=(b'\x11\x12\x13\xff\x14\x03\x15\x02\x16\x01'+
               b'\x17'+struct.pack('<d',1.25)+
               b'\x19\x31\x01\x02\x01'+  # list<bool>
               b'\x1a\x25\x00\x02'+      # set<i32>
               b'\x1b\x02\x81\x01a\x01\x01b\x02') # map<binary,bool>
        keep=item(b'unknown-fields',extra=extra)
        source=footer([keep,item(b'ARROW:schema')])
        self.assertEqual(remove_arrow_schema(source)[0],footer([keep]))
        for kind,wire in ((TRUE,b''),(FALSE,b''),(BYTE,b'\xff'),
                          (I16,b'\x03'),(I32,b'\x02'),(I64,b'\x01'),
                          (DOUBLE,b'\0'*8),(BINARY,b'\0'),(MAP,b'\0'),
                          (STRUCT,b'\x11\x00')):
            cursor=Cursor(wire);cursor.skip(kind);self.assertEqual(cursor.pos,len(wire))

    def test_explicit_field_ids_and_nested_structs(self):
        # Field ID 20 uses explicit zigzag ID, then field 21 is delta-encoded.
        keep=item(b'extended',extra=b'\x0c\x28\x11\x18\x01x\x00\x18\x01y')
        self.assertEqual(remove_arrow_schema(footer([item(b'ARROW:schema'),keep]))[0],footer([keep]))

    def test_every_truncation_and_trailing_byte_is_rejected(self):
        source=footer([item(b'kept'),item(b'ARROW:schema')])
        for stop in range(len(source)):
            with self.assertRaises(ValueError):remove_arrow_schema(source[:stop])
        with self.assertRaisesRegex(ValueError,'trailing'):remove_arrow_schema(source+b'\x00')

    def test_duplicate_and_missing_fields_are_rejected(self):
        examples=[footer([]),footer([item(b'elsewhere')]),
                  footer([item(b'ARROW:schema'),item(b'ARROW:schema')]),
                  footer([item(b'ARROW:schema',None)]),
                  footer([b'\x28\x01v\x00',item(b'ARROW:schema')]),
                  footer([b'\x18\x01k\x08\x02\x01v\x00',item(b'ARROW:schema')]),
                  footer([item(b'ARROW:schema')])[:-1]+b'\x09\x0a\x0c\x00']
        for wire in examples:
            with self.assertRaises(ValueError):remove_arrow_schema(wire)

    def test_numeric_size_type_and_depth_limits_fail_closed(self):
        for wire,bits in ((varint(2**16),16),(varint(2**32),32),(varint(2**64),64),
                          (b'\x80'*10,64)):
            with self.assertRaises(ValueError):Cursor(wire).uint(bits)
        for wire in (b'\xff\x01',b'\x0f',b'\xfc'+varint(1000001)):
            with self.assertRaises(ValueError):Cursor(wire).list()
        for value in (-1,1.5,True):
            with self.assertRaises(ValueError):varint(value)
        with self.assertRaises(ValueError):Cursor(b'\x03').skip(TRUE,container=True)
        with self.assertRaises(ValueError):Cursor(varint(1000001)).skip(MAP)
        with self.assertRaises(ValueError):Cursor(b'\x01\x0f').skip(MAP)
        with self.assertRaises(ValueError):Cursor(b'\x1c'*66+b'\x00'*67).skip(STRUCT)
        with self.assertRaises(ValueError):Cursor(b'\x0d').field(0)
        with self.assertRaises(ValueError):Cursor(b'\x08\x01').field(0)
        with self.assertRaises(ValueError):Cursor(b'\x11\x01\x02\x00').skip(STRUCT)


if __name__=='__main__':unittest.main()
