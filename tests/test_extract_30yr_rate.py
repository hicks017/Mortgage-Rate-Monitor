import unittest
from unittest.mock import patch, Mock
from src.fetch import extract_30yr_rate

class TestExtract30YrRate(unittest.TestCase):

    def setUp(self):
        self.url = "http://example.com/mortgage-rates"

    @patch("src.fetch.requests.get")
    def test_successful_rate_extraction(self, mock_get):
        # HTML contains a 30 Yr. Fixed row with a percentage value
        html = """
            <table>
              <tr>
                <th>30 Yr. Fixed</th>
                <td>3.75%</td>
              </tr>
            </table>
        """
        mock_response = Mock(status_code=200, text=html)
        mock_get.return_value = mock_response

        rate = extract_30yr_rate(self.url)
        self.assertEqual(rate, 3.75)

    @patch("src.fetch.requests.get")
    def test_raw_value_returned_on_value_error(self, mock_get):
        # HTML has non-numeric rate cell (e.g., “TBD”)
        html = """
            <table>
              <tr>
                <th>30 Yr. Fixed</th>
                <td>TBD</td>
              </tr>
            </table>
        """
        mock_response = Mock(status_code=200, text=html)
        mock_get.return_value = mock_response

        rate = extract_30yr_rate(self.url)
        self.assertEqual(rate, "TBD")

    @patch("src.fetch.requests.get")
    def test_raises_exception_on_bad_status(self, mock_get):
        # Simulate a non-200 HTTP response
        mock_response = Mock(status_code=404, text="Not Found")
        mock_get.return_value = mock_response

        with self.assertRaises(Exception) as cm:
            extract_30yr_rate(self.url)

        self.assertIn("Error fetching page: 404", str(cm.exception))

    @patch("src.fetch.requests.get")
    def test_returns_none_if_no_30yr_row(self, mock_get):
        # HTML does not include any “30 Yr. Fixed” row
        html = """
            <table>
              <tr>
                <th>15 Yr. Fixed</th>
                <td>2.85%</td>
              </tr>
            </table>
        """
        mock_response = Mock(status_code=200, text=html)
        mock_get.return_value = mock_response

        rate = extract_30yr_rate(self.url)
        self.assertIsNone(rate)


if __name__ == "__main__":
    unittest.main()
