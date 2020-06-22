<?php

namespace App\Console\Commands;

use App\Helpers\CurrencyConsole;
use Illuminate\Console\Command;

class CurrencyUpdate extends Command
{
    /**
     * The name and signature of the console command.
     *
     * @var string
     */
    protected $signature = 'update:currency';

    /**
     * The console command description.
     *
     * @var string
     */
    protected $description = 'Currency data table updater';

    /**
     * Create a new command instance.
     *
     * @return void
     */
    public function __construct()
    {
        parent::__construct();
    }

    /**
     * Execute the console command.
     *
     * @param CurrencyConsole $currencyConsole
     * @return mixed
     */
    public function handle(CurrencyConsole $currencyConsole)
    {
        $currencyConsole->getdata();
        return 'Success';
    }
}
