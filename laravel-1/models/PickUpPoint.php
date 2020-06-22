<?php

namespace App\Models\Shop;

use App\Models\Settings\Region;
use App\Scopes\StoreScope;
use App\Traits\WithStore;
use Illuminate\Database\Eloquent\{Model, SoftDeletes};

class PickUpPoint extends Model
{
    use WithStore;
    use SoftDeletes;
    public $table = 'pickup_points';
    protected $dates = ['deleted_at'];
    public $fillable = ['region_id', 'lat', 'long', 'store_id', 'name', 'address', 'description', 'work_time'];
    protected $casts = [
        'id' => 'integer',
        'region_id' => 'integer',
        'lat' => 'float',
        'long' => 'float',
        'store_id' => 'integer',
        'address' => 'string',
        'name' => 'string',
        'description' => 'description',
        'work_time' => 'work_time',
    ];

    public function region()
    {
        return $this->hasOne(Region::class, 'id', 'region_id');
    }

    public function store()
    {
        return $this->belongsTo(Store::class, 'store_id', 'id');
    }

    public function orders()
    {
        return $this->hasMany(Order::class);
    }

    protected static function boot()
    {
        parent::boot();

        static::creating(
            function ($model) {
                $model->store_id = 1;
            }
        );
        static::addGlobalScope(new StoreScope());
    }

}
