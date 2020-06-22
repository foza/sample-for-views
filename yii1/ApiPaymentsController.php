<?php
Yii::import('application.modules.orders.models.Order');
Yii::import('application.modules.orders.models.LogPayments');
Yii::import('application.modules.users.models.UserCards');

class ApiPaymentsController extends RestController
{
    public function actionPayCreate()
    {
        $this->checkAuth();
        $body = $this->parsedBody;

        $order = Order::model()->findByPk(abs(intval($body['order_id'])));

        if (!$order)
            $this->errorResponse(404, Yii::t('api', 'Order not found.'));

        if (!in_array((int)$order->payment_id, [19, 21]))
            $this->errorResponse(400);


        $card_num = isset($body['card_num']) ? filter_var($body['card_num'], FILTER_SANITIZE_NUMBER_INT) : null;
        $card_exp = isset($body['card_exp']) ? filter_var($body['card_exp'], FILTER_SANITIZE_NUMBER_INT) : null;
        $save = isset($body['save']) ? abs(intval($body['save'])) : 0;

        if(empty($card_num))
            $this->errorResponse(422, Yii::t('api', 'Card number is missing'));
        if(empty($card_exp))
            $this->errorResponse(422, Yii::t('api', 'Card expired date is missing'));


        $result = [];
        $total_price = $order->total_price + $order->delivery_price;
        switch ((int)$order->payment_id) {
            case 19: //click
                $result = $this->clickCreate($order->id, $card_num, $card_exp, $total_price, $save);
                break;
            case 21: //payme
                $result = $this->paymeCreate($order->id, $card_num, $card_exp, $total_price, $save);
                break;
        }

        if ($result['success']) {
            $this->successResponse($result['data']);
        } elseif (isset($result['errors'])) {
            $this->errorResponse(422, $result['errors']);
        } else {
            $this->errorResponse();
        }
    }


    public function actionPayConfirm()
    {
        $this->checkAuth();
        $body = $this->parsedBody;

        $pay_id = abs(intval($body['pay_id']));
        $user_id = Yii::app()->user->id;
        $code = abs(intval($body['code']));

        $model = LogPayments::model()->find('id = :id AND user_id = :user', [':id' => $pay_id, ':user' => $user_id]);

        ///N => none, C => created, V => verified, P => payed

        if (!$model)
            $this->errorResponse(404, Yii::t('api', 'Payment not found.'));

        switch ($model->pay_status) {
            case 'V':
                $this->errorResponse(422, Yii::t('api', 'Already confirmed!'));
                break;
            case 'P':
                $this->errorResponse(422, Yii::t('api', 'Already paid!'));
                break;
        }

        $result = [];

        switch ((int)$model->pay_type) {
            case 19: //click
                $result = $this->clickVerify($model, $code);
                break;
            case 21: //payme
                $result = $this->paycomVerify($model, $code);
                break;
        }


        if ($result['success']) {
            $this->successResponse();
        } elseif (isset($result['errors'])) {
            $this->errorResponse(422, $result['errors']);
        } else {
            $this->errorResponse();
        }
    }


    public function actionPayPay()
    {
        $this->checkAuth();
        $body = $this->parsedBody;

        $pay_id = abs(intval($body['pay_id']));
        $user_id = Yii::app()->user->id;

        $model = LogPayments::model()->find('id = :id AND user_id = :user', [':id' => $pay_id, ':user' => $user_id]);

        if (!$model)
            $this->errorResponse(404, Yii::t('api', 'Payment not found.'));

        // if ($model->pay_status != 'V')
        //     $this->errorResponse();

        $result = [];

        switch ((int)$model->pay_type) {
            case 19: //click
                $result = $this->clickPay($model); 
                break;
            case 21: //payme
                $result = $this->paycomPay($model);
                break;
        }

        if ($result['success']) {
            $this->successResponse();
        } elseif (isset($result['errors'])) {
            $this->errorResponse(422, $result['errors']);
        } else {
            $this->errorResponse();
        }
    }


    private function clickCreate($order_id, $number, $exp, $amount, $save = false)
    {
        $create = Yii::app()->ClickPayme->ClickCardCreate($number, $exp, $save);
        if ($create) {
            $isOk = empty($create->error_note) ? true : false;
            $paymentModel = new LogPayments();
            $paymentModel->user_id = Yii::app()->user->id;
            $paymentModel->order_id = $order_id;
            $paymentModel->pay_type = 19;
            $paymentModel->data = json_encode($create);
            $paymentModel->amount = (int)$amount;
            $paymentModel->card_num = $number;
            $paymentModel->card_exp = $exp;
            $paymentModel->created_at = time();
            $paymentModel->updated_at = time();

            if ($isOk) {
                $token = $create->card_token;
                $paymentModel->pay_status = "C";
                $paymentModel->card_token = $token;
                $paymentModel->phone_num = $create->phone_number;
                $paymentModel->is_save = $save;
                $paymentModel->save();
                return ['success' => true, 'data' => ['id' => $paymentModel->id, 'phone' => $paymentModel->phone_num]];
            } else {
                $error = $create->error_note;

                $paymentModel->save();

                return ['success' => false, 'errors' => $error];
            }
        }

        return ['success' => false];
    }

    protected function clickVerify($model, $code)
    {
        $verify = Yii::app()->ClickPayme->ClickCardVerify($model->card_token, $code);
        $model->data1 = json_encode($verify);
        $response = [];

        if (empty($verify->error_note)) {

            if ($model->is_save == 1) {
                $userModel = new UserCards();
                $userModel->user_id = $model->user_id;
                $userModel->card_num = $model->card_num;
                $userModel->card_exp = $model->card_exp;
                $userModel->card_mask = $model->card_num_mask;
                $userModel->card_token = $model->card_token;
                $userModel->pay_type = $model->pay_type;
                $userModel->created_at = time();
                $userModel->updated_at = time();
                $userModel->save();
            }

            $model->card_num_mask = $verify->card_number;
            $model->updated_at = time();
            $model->pay_status = "V";

        } else {
            $response['errors'] = $verify->error_note;
            $response['success'] = false;
            return $response;
        }
        $response['success'] = $model->save();

        return $response;
    }

    protected function clickPay($model)
    {
        $pay = Yii::app()->ClickPayme->ClickCardPayment($model->card_token, $model->amount);
        $model->data2 = json_encode($pay);
        $model->pay_status = "V";
        $response = [];

      
        if (empty($pay->error_note) || trim($pay->error_note) == "Успешно подтвержден") {
            $model->trans_id = $pay->payment_id;
            $model->pay_status = "P";
        } else {
            $response['success'] = false;
            $response['errors'] = $pay->error_note;
            $model->save();
            return $response;
        }

        $response['success'] = $model->save();

        return $response;
    }


    protected function paymeCreate($order_id, $num, $exp, $amount, $save = 0)
    {
        $amount = (int)$amount;
        $create = Yii::app()->ClickPayme->PaycomCardsCreate($num, $exp, number_format($amount, 2, '', ''), 0);

        if ($create) {
            $isOk = empty($create->error) ? true : false;
            $paymentModel = new LogPayments();
            $paymentModel->user_id = Yii::app()->user->id;
            $paymentModel->order_id = $order_id;
            $paymentModel->pay_type = 21;
            $paymentModel->data = json_encode($create);
            $paymentModel->amount = $amount;
            $paymentModel->card_num = $num;
            $paymentModel->card_exp = $exp;
            $paymentModel->created_at = time();
            $paymentModel->updated_at = time();

            if ($isOk) {
                $token = $create->result->card->token;
                $num_masked = $create->result->card->number;
                $paymentModel->card_num_mask = $num_masked;

                $verify = Yii::app()->ClickPayme->PaycomCardsGetVerifyCode($token);

                $VisOk = $verify && empty($create->error) ? true : false;
                $paymentModel->data1 = json_encode($verify);
                $paymentModel->phone_num = $verify->result->phone;

                if ($VisOk) {
                    $paymentModel->pay_status = "C";
                    $paymentModel->card_token = $token;
                    $paymentModel->is_save = $save;

                    $paymentModel->save(true);
                    return ['success' => true, 'data' => ['id' => $paymentModel->id, 'phone' => $paymentModel->phone_num]];
                } else {
                    $error = $verify->error->message;
                    $paymentModel->save();
                    return ['success' => false, 'errors' => $error];
                }
            } else {
                $error = $create->error->message;

                $paymentModel->save();
                return ['success' => false, 'errors' => $error];
            }

        }
        return ['success' => false];
    }

    protected function paycomVerify($model, $code)
    {
        $verify = Yii::app()->ClickPayme->PaycomCardsVerify($model->card_token, $code);
        $model->data2 = json_encode($verify);

        if (empty($verify->error)) {
            $model->pay_status = "V";
            $create = Yii::app()->ClickPayme->PaycomReceiptsCreate(number_format($model->amount, 2, '', ''), $model->order_id);
            $model->data3 = json_encode($create);
            $id = $create->result->receipt->_id;
            $model->trans_id = $id;

            if ($model->is_save == 1) {
                $userModel = new UserCards();
                $userModel->user_id = $model->user_id;
                $userModel->card_num = $model->card_num;
                $userModel->card_exp = $model->card_exp;
                $userModel->card_mask = $model->card_num_mask;
                $userModel->card_token = $model->card_token;
                $userModel->pay_type = $model->pay_type;
                $userModel->created_at = time();
                $userModel->updated_at = time();
                $userModel->save();
            }
        } else {
            return ['success' => false, 'errors' => $verify->error->message];
        }
        $model->updated_at = time();
        return ['success' => $model->save()];
    }

    public function paycomPay($model)
    {
        $pay = Yii::app()->ClickPayme->PaycomReceiptsPay($model->trans_id, $model->card_token);
        $model->data4 = json_encode($pay);
        $response = [];

        if (!empty($pay->error)) {
            $response['errors'] = $pay->error->message;
        } else {
            $model->pay_status = "P";
        }
        $response['success'] = $model->save();

        return $response;
    }

}

?>
