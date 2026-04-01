import React from "react";
import ReactJson from 'react-json-view';

import {DESCRIPTION, DESCRIPTION_TITLE, TITLE} from "../../../../constants/text";
import DescriptionElement from "../../atoms/DescriptionElement";
import DescriptionText from "../../atoms/DescriptionText";
import JsonBlockComponent from "../JsonBlockComponent";
import TableItem from "../../atoms/TableItem";
import CreateFileText from "../../atoms/CreateFileText";
import MethodBlock from "../../atoms/MethodBlock";
import DescriptionLink from "../../atoms/DescriptionLink";

const code =
`curl -H 'Content-Type: application/json; charset=utf-8'
     -H 'Accept: application/json'
     --data '{"jsonrpc":"2.0","method":"getToken","params":{"login":"LOGIN","password":"PASSWORD"}}'
     https://api.sweb.ru/notAuthorized/`

const GettingATokenApi = () => {

    return (
        <MethodBlock id={"getting_token_api"} title={TITLE.GETTING_A_TOKEN_API}>
            <DescriptionText >
                <p className={"content__element_text"}>
                    Для большинства запросов к API вам потребуется передавать токен, полученный после авторизации. Получить токен можно отправив следующий запрос на URL <DescriptionLink link={"https://api.sweb.ru/notAuthorized/"}/>
                </p>
            </DescriptionText>
            <DescriptionElement >
                <JsonBlockComponent object={DESCRIPTION.GETTING_A_TOKEN_API.JSON_REQUEST}
                                    id={"instruction_token_api_json_request"}
                >
                    <ReactJson src={DESCRIPTION.GETTING_A_TOKEN_API.JSON_REQUEST}
                               style={{backgroundColor: "#062436"}}
                               name={false}
                               theme={"chalk"}
                               enableClipboard={false}
                               displayObjectSize={false}
                               displayDataTypes={false}
                               displayArrayKey={false}
                    />
                </JsonBlockComponent>
            </DescriptionElement>
            <DescriptionElement >
                <DescriptionText >
                    <p style={{marginBottom: "13px"}} className={"content__element_text"}>Где:</p>

                </DescriptionText>
                {
                    DESCRIPTION.GETTING_A_TOKEN_API.TABLET.map((item, index) =>
                        <TableItem key={`description_tablet${index}`}>
                            <p className={"content__method_table-text"}><span className={"fw500"}>{item.param}</span> — {item.description}</p>
                        </TableItem>
                    )
                }
            </DescriptionElement>
            <DescriptionText>
                <p className={"content__element_text"}>
                    В ответе в параметре <span className={"fw500"}>result</span> придет токен, который нужно будет передавать при взаимодействии с API.
                </p>
            </DescriptionText>
            <DescriptionElement title={DESCRIPTION_TITLE.EXAMPLE_REQUEST}>
                <CreateFileText file={code}
                                fetchActive={false}
                                id={"instruction_token_api_example_request"}
                                className={"token_api"}
                />
            </DescriptionElement>
            <DescriptionElement title={DESCRIPTION_TITLE.EXAMPLE_RESPONSE}>
                <JsonBlockComponent object={DESCRIPTION.GETTING_A_TOKEN_API.JSON_RESPONSE}
                                    id={"instruction_token_api_json_response"}
                >
                    <ReactJson src={DESCRIPTION.GETTING_A_TOKEN_API.JSON_RESPONSE}
                               style={{backgroundColor: "#062436"}}
                               name={false}
                               theme={"chalk"}
                               enableClipboard={false}
                               displayObjectSize={false}
                               displayDataTypes={false}
                               displayArrayKey={false}
                    />
                </JsonBlockComponent>
            </DescriptionElement>
        </MethodBlock>
    )
}

export default GettingATokenApi