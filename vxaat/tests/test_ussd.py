from twisted.internet.defer import inlineCallbacks

from vumi.tests.helpers import VumiTestCase
from vumi.transports.httprpc.tests.helpers import HttpRpcTransportHelper

from vxaat.ussd import AatUssdTransport


class TestAatUssdTransport(VumiTestCase):
    _from_addr = '27729042520'
    _to_addr = '1234'
    _request_defaults = {
        'msisdn': _from_addr,
        'request': "He's not dead, he is pining for the fjords",
        'provider': 'MTN',
    }

    @inlineCallbacks
    def setUp(self):
        self.config = {
            'base_url': "http://www.example.com:42666",
            'web_path': '/api/v1/aat/ussd/',
            'web_port': '0',
            'suffix_to_addrs': {
                'some-suffix': self._to_addr,
                'some-more-suffix': '4321'
            }
        }
        self.tx_helper = self.add_helper(
            HttpRpcTransportHelper(
                AatUssdTransport,
                request_defaults=self._request_defaults
            )
        )
        self.transport = yield self.tx_helper.get_transport(self.config)
        self.transport_url = self.transport.get_transport_url(
            self.config['web_path']
        )

    def callback_url(self):
        #Not sure if I should reconstruct it here.
        return "http://www.example.com:42666/api/v1/aat/ussd/some-suffix"

    def assert_inbound_message(self, msg, **field_values):
        expected_field_values = {
            'content': self._request_defaults['request'],
            'to_addr': '1234',
            'from_addr': self._request_defaults['msisdn'],
        }
        expected_field_values.update(field_values)
        for field, expected_value in expected_field_values.iteritems():
            self.assertEqual(msg[field], expected_value)

    def assert_outbound_message(self, msg, content, callback):

        xml = '<request>' \
              '<headertext>%s</headertext>' \
              '<options>' \
              '<option callback="%s" command="1" display="false" order="1" />' \
              '</options>' \
              '</request>' % (content, callback)
        self.assertEqual(msg, xml)

    @inlineCallbacks
    def test_inbound_begin(self):

        # Make contact
        user_content = "Blessed are the cheesemakers!"
        d = self.tx_helper.mk_request('some-suffix', request=user_content)
        [msg] = yield self.tx_helper.wait_for_dispatched_inbound(1)

        self.assert_inbound_message(
            msg,
            content=user_content
        )

        reply_content = 'We are the Knights Who Say ... Ni!'
        reply = msg.reply(reply_content)
        self.tx_helper.dispatch_outbound(reply)
        response = yield d

        self.assert_outbound_message(response.delivered_body, reply_content, self.callback_url())