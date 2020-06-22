<?php

use Laravel\Passport\Token;
use Lcobucci\JWT\Parser;

if (!function_exists('client')) {
    function client($force = false)
    {
        $JWTParser = new Parser();
        $bearerToken = request()->bearerToken();
        if (empty($bearerToken) && $force) {
            return Token::with(['client'])->first()->client;
        }
        $tokenId = $JWTParser->parse($bearerToken)->getHeader('jti');

        return Token::find($tokenId)->client;
    }
}
