export const TITLE = {
    BROWSER_TITLE: "API Spaceweb",
    EXAMPLE_API: "Примеры использования API",

    INSTRUCTION: "Инструкция по взаимодействию с API",
    CALLING_THE_API: "Обращение к API метод",
    GETTING_A_TOKEN_API: "Получение токена для взаимодействия с API",
    EXAMPLE_FORM_REQUEST: "Пример формата запроса",
    SUCCESSFUL_RESPONSE: "Успешный ответ",
    ERROR_MESSAGE: "Сообщение об ошибке",
    EXTENDED_MESSAGE_ABOUT_RESPONSE: "Расширенное сообщение о результатах работы метода"
}

export const DESCRIPTION_TITLE = {
    DESCRIPTION: "описание",
    APPLICABILITY: "применяемость",
    PATH_TO_OBJECT: "путь к объекту",
    AUTHORIZATION_REQUIREMENT: "требование к авторизации",
    LIST_METHODS: "список методов",
    RETURN_VALUES: {
        ARRAY: "возвращаемые значения в свойствах элементов массива",
        OBJECT: "возвращаемые значения в свойствах объекта",
        OTHER: "возвращаемое значение"
    },
    PARAMS_TO_REQUEST: "параметры в запросе",
    TYPE_DATA_RESPONSE: "тип данных в ответе",
    EXAMPLE_REQUEST: "пример запроса",
    EXAMPLE_RESPONSE: "пример ответа",

    ACTUAL_VERSION: "актуальная версия используемой спецификации",
    REQUEST_URL: "request URL",
    TITLES_REQUEST: "заголовки запроса",
    POST_REQUEST: "POST данные в запросе",
    PARAMS_DESCRIPTION: "описание параметров"
}
export const DESCRIPTION = {
    GETTING_A_TOKEN_API: {
        JSON_REQUEST: {
            "jsonrpc":"2.0",
            "method":"getToken",
            "params": {
                "login":"<ваш логин>",
                "password":"<ваш пароль>"
            }
        },
        TABLET: [
            {
                param: "<ваш логин>",
                description: "логин в Личный кабинет аккаунта"
            },
            {
                param: "<ваш пароль>",
                description: "пароль в Личный кабинет аккаунта"
            }
        ],
        JSON_RESPONSE: {
            "jsonrpc":"2.0",
            "id":"20220505104244.40FxsQ16Ff",
            "result":"hdlhcdkd0bid6c29fhfu1s7123.202357ec-d5ca-4a0a-846c-2dabe0266ef4"
        }
    },
    EXAMPLE_FORM_REQUEST: {
        JSON: {
            "jsonrpc":"2.0",
            "method":"move",
            "params":{
                "domain":"vpstest.ru"
            },
            "id":"20183994338.43VSEkfGFh",
            "user":"vhp****"
        },
        TABLET: [
            {
                param: "jsonrpc",
                description: "текущая версия JSON-RPC"
            },
            {
                param: "version",
                description: "текущая версия клиента приложения. Носит только информационный характер, используется в отчетах об ошибках"
            },
            {
                param: "method",
                description: "метод объекта Domains"
            },
            {
                param: "params",
                description: "объект параметров метода (ключ элемента объекта - имя параметра)"
            },
            {
                param: "id",
                description: "уникальный идентификатор запроса"
            },
            {
                param: "user",
                description: "логин пользователя, который отправляет запрос. Носит только информационный характер, сверяется со значением сессии токена и в случае расхождения приводит к ошибке авторизации"
            },
        ]
    },
    SUCCESSFUL_RESPONSE: {
        JSON: {
            "jsonrpc":"2.0",
            "id":"20183995523.MO4E9baKRr",
            "result":{
                "balance":{
                    "real_balance":500,
                    "bonus_balance":0
                }
            }
        },
        TABLET: [
            {
                param: "jsonrpc",
                description: "текущая версия JSON-RPC"
            },
            {
                param: "version",
                description: "текущая версия клиента"
            },
            {
                param: "result",
                description: "результат, который возвращает вызванный метод"
            },
            {
                param: "id",
                description: "уникальный идентификатор ответа, если был в запросе, то совпадает с ним"
            },
        ]
    },
    ERROR_MESSAGE: {
        JSON: {
            "jsonrpc":"2.0",
            "version":"0.1",
            "id":"20183910121.UPNWsDxwmn",
            "error":{
                "code":-32601,
                "message":"Object not found"
            }
        },
        TABLET: [
            {
                param: "jsonrpc",
                description: "текущая версия JSON-RPC"
            },
            {
                param: "version",
                description: "текущая версия клиента"
            },
            {
                param: "error",
                description: "<b>данные</b> разного типа <b>вот тако вот</b>"
            },
            {
                param: "id",
                description: "уникальный идентификатор ответа, если был в запросе, то совпадает с ним"
            },
        ]
    },
    EXTENDED_MESSAGE_ABOUT_RESPONSE: {
        JSON: {
            FIRST: {
                "jsonrpc": "2.0",
                "id": "20183995523.MO4E9baKRr",
                "result": {
                    "extendedResult": {
                        "code": 1,
                        "message": "\u0417\u0430\u044f\u0432\u043a\u0430 #180047823 \u043f\u0440\u0438\u043d\u044f\u0442\u0430 \u0432 \u0440\u0430\u0431\u043e\u0442\u0443",
                        "data": []
                    }
                }
            },
            SECOND: {
                "jsonrpc":"2.0",
                "id":"20183995523.MO4E9baKRr",
                "result": {
                    "extendedResult": {
                        "code": 0,
                        "message": "\u0417\u043e\u043d\u0430 .child \u043d\u0435 \u043f\u043e\u0434\u0434\u0435\u0440\u0436\u0438\u0432\u0430\u0435\u0442\u0441\u044f \u0434\u043b\u044f \u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0430\u0446\u0438\u0438",
                        "data": []
                    }
                }
            }
        },
        TABLET: [
            {
                param: "code",
                description: "1 - успешное выполнение, 0 - ошибка"
            },
            {
                param: "message",
                description: "кастомизированное сообщение о результате"
            },
            {
                param: "data",
                description: "объект дополнительных данных (может быть пустым)"
            },
        ]
    }
}