<?php

namespace App\Http\Controllers\Api\v1\Currency;

use App\Http\Controllers\Api\v1\BaseController;
use App\Repositories\CurrencyRepository;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class CurrencyController extends BaseController
{
    private $currencyRepository;

    /**
     * CurrencyController constructor.
     * @param CurrencyRepository $currencyRepository
     */
    public function __construct(CurrencyRepository $currencyRepository)
    {
        $this->currencyRepository = $currencyRepository;
    }

    /**
     * @param int $id
     * @param Request $request
     * @return JsonResponse
     */
    public function getById(int $id, Request $request): JsonResponse
    {
        return $this->responseWithData($this->currencyRepository->getById($id));
    }

    public function all()
    {
        return $this->responseWithData($this->currencyRepository->all());
    }
}
