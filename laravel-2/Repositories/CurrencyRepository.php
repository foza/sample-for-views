<?php

namespace App\Repositories;

use App\Models\Currency;
use App\Repositories\Interfaces\CurrencyInterfaces;
use Prettus\Repository\Eloquent\BaseRepository;

class CurrencyRepository implements CurrencyInterfaces
{
    /**
     * @inheritDoc
     */
    public function model()
    {
        return Currency::class;
    }

    public function getById(int $id)
    {
        return Currency::where('id',$id)->get();
    }

    public function all()
    {
        return Currency::paginate();
    }
}
