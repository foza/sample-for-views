<?php

namespace App\Repositories;

use Illuminate\Http\Request;
use App\Criteria\UserIdCriteria;
use App\Models\Shop\Notification;
use Prettus\Repository\Eloquent\BaseRepository;

class NotificationRepository extends BaseRepository
{

    public function getUserNotifications(Request $request)
    {
        $this->pushCriteria(UserIdCriteria::class);
        $this->orderBy('id', 'desc');

        return $this->paginate();
    }

    public function changeRead(int $id)
    {
        $this->pushCriteria(UserIdCriteria::class);
        $notification = $this->find($id);
        $notification->read = true;
        $notification->update();
        return $this->paginate();
    }

    public function getUserNotification(int $id)
    {
        $this->pushCriteria(UserIdCriteria::class);

        return $this->find($id);
    }

    /**
     * @inheritDoc
     */
    public function model()
    {
        return Notification::class;
    }
}
