<?php

namespace App\Helpers;

use App\Models\Currency;

class CurrencyConsole
{
    /**
     * @return array
     */
    private function getCurrency()
    {
        try {
            $handler = new CurrencyDaily();
            return $handler
                ->request()
                ->getResult();
        } catch (\Exception $e) {
            echo $e->getMessage();
        }
    }

    /**
     *  show
     */
    public function getData()
    {
        $melts = $this->getCurrency();
        foreach ($melts as $key => $value) {
            $currency = new Currency();
            $currency->name = $value['Name'];
            $currency->rate = $value['Value'];
            $currency->save();
        }
    }

}
