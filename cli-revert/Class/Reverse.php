<?php

class Reverse
{
    /**
     * @var
     */
    private $string;

    /**
     * Reverse constructor.
     * @param $string
     */
    public function __construct($string)
    {
        $this->string = $string;
    }


    /**
     * @return string
     */
    public function convert(): string
    {
        $st = mb_strtolower($this->string);
        $stringArray = explode(' ', $st);
        $revert_str = '';
        for ($i = 0; $i < count($stringArray); $i++) {
            $str_part = $this->strRev($stringArray[$i]);
            if (!preg_match('/^[a-zа-яё ]+$/ui', $str_part)) {
                $symbol = mb_substr($str_part, 0, 1);
                $string = mb_substr($str_part, 1);
                $str_part = $string.$symbol;
            }
            $revert_str .= ' ' . $str_part;
        }
        return mb_convert_case($revert_str, MB_CASE_TITLE, "UTF-8");
    }

    /**
     * @param $str
     * @return string
     */
    public function strRev($str): string
    {
        preg_match_all('/./us', $str, $ar);
        return join('', array_reverse($ar[0]));
    }
}