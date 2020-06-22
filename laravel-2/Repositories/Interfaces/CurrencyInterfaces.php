<?php

namespace App\Repositories\Interfaces;

use App\Models\Currency;

interface CurrencyInterfaces
{
    /**
     * @return mixed
     */
    public function all();

    /**
     * @param int $id
     * @return Currency
     */
    public function getById(int $id);
}
