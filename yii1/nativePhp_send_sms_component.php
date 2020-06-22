<?php
require_once "include/HttpClient.php";
require_once "include/JSON.php";
class Sms  {
    public $url = 'http://smsgw.vas.uz:8808/api/send';
    public $login = '*';
    public $pass = '*';


    protected $_error_codes = array(
        1 => 'Ошибка при отправке СМС',
        10 => 'Необходимо указать Логин',
        11 => 'Не указан ключ',
        12 => 'partner not found',
        13 => 'wrong key',
        14 => 'phone required',
        15 => 'sender required',
        16 => 'wrong sender',
        17 => 'phone not match to pattern',
        18 => 'text required',
        19 => 'text too long',
        20 => 'receiver in blacklist',
    );

    protected $_error_code;


    // initialize SMS
    public function init() {

    }

    public function send($number,$text, $translit = false)
    {
        $url = $this->url;

        if($translit)
        {
            $text = $this->rus2translit($text);
        }

        // generate provider code by mobile phone number
        $provider = self::getProviderCodeByNumber($number);
        if ( !$provider )
            return false;



        $postdata = array(
            'login'    => $this->login,
            'key' 	   => $this->pass,
            'text'     => iconv('UTF-8', 'UTF-8', $text),
            'phone'    => $number,
            'sender'   => 'Bringo.uz',
        );

        $data = http_build_query($postdata);
        $json = new Services_JSON();
        $output = HttpClient::doRequest($url, $data);
        $result = $json->decode($output);

        if($result->code == 0)return true;

        else{
            $this->_error_code = $result->code;
            return false;
        }
    }


    public function getError()
    {
        if($this->_error_code && isset($this->_error_codes[$this->_error_code]))
        {
            return $this->_error_codes[$this->_error_code];
        }
        else
        {
            return false;
        }
    }



    public function getProviderCodeByNumber( $number )
    {
        // only numeric symbols
        if ( preg_match('/^[0-9]+$/', $number) == false )
            return false;
        // if full number rrrppnnnnnnn r = region, p = provider, n = number. Valid length is 12 symbols
        if ( strlen($number) != 12 )
            return false;

        $codes = array(
            // Beeline
            '90' => 'beeline4447',
            '91' => 'beeline4447',
            // Ucell
            '93' => 'ucell4447',
            '94' => 'ucell4447',
            // Uzmobile
            '95' => 'uzmobile4447',
            '99' => 'uzmobile4447',
            // UMS
            '97' => 'ums4447',
            // Perfectum mobile
            '98' => 'perfectum4447',
        );

        return ( !empty( $codes[substr($number, 3, 2)] ) ? $codes[substr($number, 3, 2)] : false );
    }


    public function rus2translit($string) {
        $converter = array(
            'а' => 'a',   'б' => 'b',   'в' => 'v',
            'г' => 'g',   'д' => 'd',   'е' => 'e',
            'ё' => 'e',   'ж' => 'zh',  'з' => 'z',
            'и' => 'i',   'й' => 'y',   'к' => 'k',
            'л' => 'l',   'м' => 'm',   'н' => 'n',
            'о' => 'o',   'п' => 'p',   'р' => 'r',
            'с' => 's',   'т' => 't',   'у' => 'u',
            'ф' => 'f',   'х' => 'h',   'ц' => 'c',
            'ч' => 'ch',  'ш' => 'sh',  'щ' => 'sch',
            'ь' => '\'',  'ы' => 'y',   'ъ' => '\'',
            'э' => 'e',   'ю' => 'yu',  'я' => 'ya',

            'А' => 'A',   'Б' => 'B',   'В' => 'V',
            'Г' => 'G',   'Д' => 'D',   'Е' => 'E',
            'Ё' => 'E',   'Ж' => 'Zh',  'З' => 'Z',
            'И' => 'I',   'Й' => 'Y',   'К' => 'K',
            'Л' => 'L',   'М' => 'M',   'Н' => 'N',
            'О' => 'O',   'П' => 'P',   'Р' => 'R',
            'С' => 'S',   'Т' => 'T',   'У' => 'U',
            'Ф' => 'F',   'Х' => 'H',   'Ц' => 'C',
            'Ч' => 'Ch',  'Ш' => 'Sh',  'Щ' => 'Sch',
            'Ь' => '\'',  'Ы' => 'Y',   'Ъ' => '\'',
            'Э' => 'E',   'Ю' => 'Yu',  'Я' => 'Ya',
        );
        return strtr($string, $converter);
    }

}