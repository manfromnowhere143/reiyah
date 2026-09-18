"""Bounded Thrift Compact cursor for one lossless Parquet footer-key removal.

Only FileMetaData.key_value_metadata (field 5) is interpreted. All surviving
field and list-item bytes are copied verbatim, including unknown fields.
"""
import hashlib

from packet_core import require


STOP, TRUE, FALSE, BYTE, I16, I32, I64, DOUBLE, BINARY, LIST, SET, MAP, STRUCT = range(13)


def varint(value):
    require(type(value) is int and value >= 0,'Invalid unsigned integer')
    out=bytearray()
    while value>=128:out.append((value&127)|128);value>>=7
    out.append(value);return bytes(out)


def list_header(count,kind):
    require(type(count) is int and 0<=count<=1000000 and 1<=kind<=12,'Invalid list header')
    return bytes([(min(count,15)<<4)|kind])+(varint(count) if count>=15 else b'')


class Cursor:
    def __init__(self,raw):
        require(isinstance(raw,bytes) and len(raw)<=64*1024**2,'Invalid footer bytes')
        self.raw=raw;self.pos=0

    def take(self,count):
        require(type(count) is int and count>=0 and self.pos+count<=len(self.raw),'Truncated compact value')
        value=self.raw[self.pos:self.pos+count];self.pos+=count;return value

    def byte(self):return self.take(1)[0]

    def uint(self,bits=64):
        result=0
        for shift in range(0,70,7):
            byte=self.byte();result|=(byte&127)<<shift
            if byte<128:
                require(result<1<<bits,'Compact integer overflow');return result
        raise ValueError('Unterminated compact integer')

    def binary(self):return self.take(self.uint(32))

    def field(self,previous):
        header=self.byte()
        if header==STOP:return None
        kind=header&15;delta=header>>4
        require(1<=kind<=12,'Unsupported compact field type')
        if delta:identifier=previous+delta
        else:
            encoded=self.uint(16);identifier=(encoded>>1)^-(encoded&1)
        require(0<identifier<32768,'Invalid compact field ID')
        return identifier,kind

    def list(self):
        header=self.byte();size=header>>4;kind=header&15
        if size==15:size=self.uint(32)
        require(size<=1000000 and 1<=kind<=12,'Invalid compact collection')
        return size,kind

    def skip(self,kind,depth=0,container=False):
        require(depth<=64,'Compact nesting limit')
        if kind in (TRUE,FALSE):
            if container:require(self.byte() in (TRUE,FALSE),'Invalid compact boolean')
        elif kind==BYTE:self.take(1)
        elif kind in (I16,I32,I64):self.uint({I16:16,I32:32,I64:64}[kind])
        elif kind==DOUBLE:self.take(8)
        elif kind==BINARY:self.binary()
        elif kind in (LIST,SET):
            size,element=self.list()
            for _ in range(size):self.skip(element,depth+1,True)
        elif kind==MAP:
            size=self.uint(32);require(size<=1000000,'Compact map limit')
            if size:
                types=self.byte();key,value=types>>4,types&15
                require(1<=key<=12 and 1<=value<=12,'Invalid compact map type')
                for _ in range(size):self.skip(key,depth+1,True);self.skip(value,depth+1,True)
        elif kind==STRUCT:
            previous=0;seen=set()
            while (field:=self.field(previous)) is not None:
                previous,child=field;require(previous not in seen,'Duplicate compact field');seen.add(previous)
                self.skip(child,depth+1)
        else:raise ValueError('Unsupported compact type')


def remove_arrow_schema(footer):
    cursor=Cursor(footer);previous=0;seen=set();patch=None;removed=None
    while (field:=cursor.field(previous)) is not None:
        previous,kind=field;require(previous not in seen,'Duplicate footer field');seen.add(previous)
        if previous!=5:
            cursor.skip(kind);continue
        require(kind==LIST,'Footer key/value field is not a list')
        begin=cursor.pos;size,item_type=cursor.list();require(item_type==STRUCT,'Metadata entries are not structs')
        survivors=[];keys=set()
        for _ in range(size):
            item_begin=cursor.pos;item_previous=0;item_seen=set();key=value=None
            while (item:=cursor.field(item_previous)) is not None:
                item_previous,item_kind=item
                require(item_previous not in item_seen,'Duplicate key/value field');item_seen.add(item_previous)
                if item_previous in (1,2):
                    require(item_kind==BINARY,'Metadata key/value is not binary')
                    data=cursor.binary()
                    if item_previous==1:key=data
                    else:value=data
                else:cursor.skip(item_kind)
            require(key is not None and key not in keys,'Missing or duplicate metadata key');keys.add(key)
            if key==b'ARROW:schema':
                require(value is not None,'Serialized Arrow schema has no value');removed=value
            else:survivors.append(footer[item_begin:cursor.pos])
        end=cursor.pos
        patch=(begin,end,list_header(len(survivors),STRUCT)+b''.join(survivors))
    require(cursor.pos==len(footer),'Unparsed trailing footer bytes')
    require(patch is not None and removed is not None,'Serialized Arrow schema entry absent')
    begin,end,replacement=patch
    result=footer[:begin]+replacement+footer[end:]
    return result,{'removed_schema_sha256':hashlib.sha256(removed).hexdigest(),
                   'original_list_payload_start':begin,'original_list_payload_end':end,
                   'replacement_list_payload_bytes':len(replacement),
                   'all_surviving_footer_field_bytes_preserved':True}
