<?php

require_once 'Class/Reverse.php';

$string = readline("Нажмите [1] для ввода текста: \nНажмите [0] дефаултный [Привет! Давно не виделись.]: ");
if ($string == 0){
    $res = new Reverse('Привет! Давно не виделись.');
    print $res->convert();
}else{
    $command = readline('Введите слово:');
    $res = new Reverse($command);
    print $res->convert();
}

?>