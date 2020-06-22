<?php

namespace App\Helpers;
/**
 * Class CurrencyDaily
 * @package CBR
 */
class CurrencyDaily
{
    private $date;
    private $codes;
    private $result;
    private $result_date;

    const KEY_CHAR = 1;
    const KEY_NUM = 2;
    const KEY_ID = 3;
    const KEY_CODE = 0;


    /**
     * @param $date
     * @return $this
     */
    public function setDate($date)
    {
        $this->date = $date;

        return $this;
    }

    /**
     * @param $codes
     * @return $this
     */
    public function setCodes($codes)
    {
        if (!is_array($codes)) {
            $codes = [$codes];
        }

        $this->codes = $codes;

        return $this;
    }

    /**
     * @param string $format
     * @return mixed
     * 'Y-m-d'
     */
    public function getResultDate($format = 'Y/m/d')
    {
        return $this->result_date->format($format);
    }

    /**
     * @return $this
     */
    public function request()
    {
        $this->result = (new Request(Request::URL_CUR_DAILY, [
            'date_req' => ((empty($this->date)) ? null : $this->date)
        ]))->request();

        return $this;
    }

    /**
     * @param int $key
     * @return array
     * @throws \Exception
     */
    public function getResult($key = self::KEY_CHAR)
    {
        libxml_use_internal_errors(true);
        $xml = new \SimpleXMLElement($this->result);

        $date = str_replace('.0', '.', (string)$xml->attributes()['Date']);
        $this->result_date = (new \DateTime())->setTimestamp(strtotime($date));

        if (empty($this->codes)) {
            $xpath = $xml->xpath('Valute');
            $result = [];
            foreach ($xpath as $element) {
                switch ($key) {
                    case self::KEY_CHAR:
                        $k = (string)$element->CharCode;
                        break;
                    case self::KEY_NUM:
                        $k = (string)$element->NumCode;
                        break;
                    case self::KEY_ID:
                        $k = (string)$element->attributes()['ID'];
                        break;
                }

                $result[$k] = [
                    'ID' => (string)$element->attributes()['ID'],
                    'NumCode' => (string)$element->NumCode,
                    'CharCode' => (string)$element->CharCode,
                    'Nominal' => (int)$element->Nominal,
                    'Name' => (string)$element->Name,
                    'Value' => (float)(str_replace(',', '.', $element->Value))
                ];
            }

            return $result;
        }

        $length = count($this->codes);

        if ($length > 1) {
            $codes = 'CharCode = "' . $this->codes[0] . '"';
            for ($i = 1; $i < $length; $i++) {
                $codes .= ' or CharCode = "' . $this->codes[$i] . '"';
            }
        } else {
            $codes = 'CharCode = "' . $this->codes[0] . '"';
        }

        $xpath = $xml->xpath('Valute[' . $codes . ']');
        $result = [];
        foreach ($xpath as $element) {
            $k = 0;
            $result[$k] = [
                'ID' => (string)$element->attributes()['ID'],
                'NumCode' => (string)$element->NumCode,
                'CharCode' => (string)$element->CharCode,
                'Nominal' => (int)$element->Nominal,
                'Name' => (string)$element->Name,
                'Value' => (float)(str_replace(',', '.', $element->Value))
            ];
        }

        return $result;
    }

    /**
     * @return mixed
     */
    public function getResultXML()
    {
        return $this->result;
    }
}
