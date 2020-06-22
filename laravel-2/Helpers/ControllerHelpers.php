<?php

namespace App\Helpers;

use Illuminate\{Http\JsonResponse, Pagination\LengthAwarePaginator};

trait ControllerHelpers
{

    protected $message = 'Данные загружены';

    /**
     * JsonResponse с данными
     *
     * @param array $data
     * @param string $status
     * @param int $statusCode
     *
     * @return JsonResponse
     */

    protected function responseWithData($data = [], string $status = 'ok', int $statusCode = 200): JsonResponse
    {
        list(, $routeMethod) = explode('@', request()->route()->getActionName());
        $response = [];
        switch ($routeMethod) {
            case 'store':
                $this->setMessage('Ресурс создан');
                $statusCode = 201;
                break;
            case 'update':
                $this->setMessage('Ресурс обновлен');
                break;
            case 'destroy':
                $this->setMessage('Ресурс удален');
                break;
        }
        $response['message'] = $this->message;
        $response['status'] = $status;
        $response['data'] = $data;
        $response['paginator'] = null;
        if ($data instanceof LengthAwarePaginator) {
            $dataArray = $data->toArray();
            $response['data'] = $dataArray['data'];
            unset($dataArray['data']);
            $response['paginator'] = $dataArray;
        }

        return $this->responseWith($response, $statusCode);
    }

    /**
     * JsonResponse с сообщением
     *
     * @param string $message
     * @param string $status
     * @param int $statusCode
     *
     * @return JsonResponse
     */

    protected function responseWithMessage(string $message, string $status = 'ok', int $statusCode = 200): JsonResponse
    {
        $response = [
            'status' => $status,
            'message' => $message,
        ];

        return $this->responseWith($response, $statusCode);
    }


    /**
     * @param array $errors
     * @return JsonResponse
     */
    protected function responseWithValidate($errors = []):JsonResponse{
        $response = [
            'error' => "error",
            'message' => 'Параметры не прошли валидацию',
            'errors'=>$errors
        ];
        return response()->json($response);
    }

    /**
     * Генерировать JsonResponse
     *
     * @param array $response
     * @param int $statusCode
     *
     * @return JsonResponse
     */

    private function responseWith(array $response, int $statusCode): JsonResponse
    {
        return response()->json($response)->setStatusCode($statusCode);
    }

    /**
     * Установить сообщение
     *
     * @param $message
     *
     * @return $this
     */
    protected function setMessage($message): self
    {
        $this->message = $message;

        return $this;
    }
}
