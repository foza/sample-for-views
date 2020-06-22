<?php

namespace App\Models\Shop;

use App\Models\{Products\Product, Products\ProductType, Users\User};
use Carbon\Carbon;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\Model;

class Discount extends Model
{

    protected $fillable = ['name', 'type', 'value', 'valid_from', 'valid_until', 'store_id', 'entity'];
    protected $dates = ['valid_from', 'valid_until'];
    protected $casts = [
        'valid_from' => 'date_format:d-m-Y H:i:s',
        'valid_until' => 'date_format:d-m-Y H:i:s',
        'store_id' => 'integer',
    ];

    public function products()
    {
        return $this->belongsToMany(Product::class);
    }

    public function product_types()
    {
        return $this->belongsToMany(ProductType::class);
    }

    public function users()
    {
        return $this->hasMany(User::class);
    }

    public function store()
    {
        return $this->belongsTo(Store::class);
    }

    public function scopeActive(Builder $query)
    {
        $now = Carbon::now();
        return $query->where('valid_from', '<=', $now)->where('valid_until', '>=', $now);
    }
}
