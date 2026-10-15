"""本地stdio协议回归，不连接云端，也不读取凭证。"""
import os
import sys
import unittest
from tools.cloudbase_mcp import stdio_call


SERVER = '''
import sys,json
for line in sys.stdin:
    message=json.loads(line)
    if 'id' not in message: continue
    if message['method']=='initialize': result={'protocolVersion':'2024-11-05','capabilities':{},'serverInfo':{'name':'fixture','version':'1'}}
    else:
        print(json.dumps({'jsonrpc':'2.0','method':'notifications/progress','params':{}}),flush=True)
        arguments=message['params']['arguments']
        result={'isError':True,'content':[{'type':'text','text':'secret-must-not-escape'}]} if arguments.get('fail') else {'content':[{'type':'text','text':json.dumps(arguments,ensure_ascii=False)}]}
    print(json.dumps({'jsonrpc':'2.0','id':message['id'],'result':result},ensure_ascii=False),flush=True)
'''


class StdioTests(unittest.TestCase):
    def test_chinese_arguments_and_notifications(self):
        result = stdio_call([sys.executable, '-u', '-c', SERVER], os.environ.copy(), 'fixture', {'name': '半导体', 'path': r'C:\测试'}, timeout=5)
        self.assertEqual(result, {'name': '半导体', 'path': r'C:\测试'})

    def test_error_does_not_expose_response(self):
        with self.assertRaises(RuntimeError) as captured:
            stdio_call([sys.executable, '-u', '-c', SERVER], os.environ.copy(), 'fixture', {'fail': True}, timeout=5)
        self.assertNotIn('secret-must-not-escape', str(captured.exception))


if __name__ == '__main__':
    unittest.main()
