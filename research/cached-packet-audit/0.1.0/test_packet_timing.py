import unittest
from packet_timing import align,expected_vector


def image(i):
    return {'image_id':str(i),'rows':1,'first_row':i,'metadata':{'capture_ms':i+.1,
            'timing':{'preprocess':i*1000000+333333,'inference':i*1000000+222222,'decode':111111},'emit_ts_ns':i}}


def chart(images):
    vectors=[expected_vector(r,'float32_stages') for r in images]
    return {'series':[{'name':name,'data':[{'x':i,'y':v[j]} for i,v in enumerate(vectors)]}
                     for j,name in enumerate(['capture_ms','preprocess_ms','inference_ms','postprocess_ms'])]}


class TimingControls(unittest.TestCase):
    def test_known_five_omissions_with_complete_tuple_match(self):
        images=[image(i) for i in range(8)];result=align(images,chart(images[5:]))
        matches=[r for r in result['trials'] if r['all_tuples_match']]
        self.assertEqual(len(matches),3);self.assertTrue(all(r['offset']==5 for r in matches))
        self.assertFalse(result['historical_warmup_intention_established'])

    def test_matching_one_component_does_not_match_tuple(self):
        images=[image(i) for i in range(8)];c=chart(images[5:]);c['series'][2]['data'][1]['y']+=1
        self.assertEqual(align(images,c)['matching_trials'],0)

    def test_missing_timing_is_not_zero(self):
        images=[image(i) for i in range(8)];c=chart(images[5:]);images[6]['metadata']['timing']=None
        self.assertEqual(align(images,c)['matching_trials'],0)

    def test_malformed_chart_rejected(self):
        images=[image(i) for i in range(8)];c=chart(images[5:]);c['series'][0]['data'][0]['x']=9
        with self.assertRaisesRegex(ValueError,'index'):align(images,c)


if __name__=='__main__':unittest.main()
