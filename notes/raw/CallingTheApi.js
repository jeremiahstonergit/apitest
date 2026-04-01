import React from "react";
import {TITLE} from "../../../../constants/text";
import MethodBlock from "../../atoms/MethodBlock";
import DescriptionText from "../../atoms/DescriptionText";

const CallingTheApi = () => {

    return (
        <MethodBlock id={"calling_the_api"} title={TITLE.CALLING_THE_API}>
            <DescriptionText >
                <p className={"content__element_text"}>
                    Обращение к API происходит по протоколу HTTP/HTTPS и использует метод POST передачи данных в виде JSON. В самом запросе URI указывает на объект (класс), а тело запроса содержит метод этого класса и параметры вызова.
                    <br></br><br></br>
                    Метод по умолчанию для всех объектов <span className={"fw500"}>«index»</span>.
                </p>
            </DescriptionText>
        </MethodBlock>
    )
}

export default CallingTheApi;