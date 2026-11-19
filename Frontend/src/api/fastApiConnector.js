//fastApiConnector

import
{
    BASE_URL
}
    from '../constants/config'//importujemy z innego pliku

export const sendTextToFastAPI = async (
    text,
    sessionID,
    attachedFile = null,
    isAdmin = false,
    onStatusChange = null
) =>
{
    const fastApiRequestDataForm = new FormData();//aby dodać pdf'a trzeba stworzyć forma

    //nazwy pól muszą się zgadzać z tym co jest w main.py (backend)
    fastApiRequestDataForm.append(
        'sessionID',
        sessionID
    );
    fastApiRequestDataForm.append(
        'request',
        text
    );

    if (attachedFile) {
        fastApiRequestDataForm.append(
            'attachedFile',
            attachedFile
        )
    }

    fastApiRequestDataForm.append(
        'isAdmin', isAdmin
    );




    try {
        const responseFromBackend = await fetch(
            `${BASE_URL}/chat`,
            {
            method: 'POST',
            body: fastApiRequestDataForm
            }
        );

        if (!responseFromBackend.ok)
        {
            throw new Error(
                'Błąd połączenia sieci z FastAPI'
            );
        }

        const textDecoder = new TextDecoder();//dane to surowe bajty


        let streamBuffer = '';



        const toolCallingOutputStreamReader = responseFromBackend.body.getReader();//odczyt kawałek po kawa�ku
        

        let streamOutput = '';
        while (true)//działa tak długo, aż stream się nie zakończy
        {           //nazwy te są zdefiniowane przez reacta
            const {
                done, value
            } = await toolCallingOutputStreamReader.read();//czeka na wywołanie narzędzia

            if (done)
            {
                break;
            }


            streamBuffer = streamBuffer + textDecoder.decode(
                value,
                {
                    stream: true
                }
            );

            const lines = streamBuffer.split('\n');

            let poppedLines = lines.pop();
            //ostatnia linijka może nie być pełna
            streamBuffer = poppedLines;
            for (const line of lines)// of nie in
            {

                if (line.trim() != '')//wyciągamy wartości z pól
                {
                    try
                    {
                        const dataExtractedFromJson = JSON.parse(line);

                        if (dataExtractedFromJson.type === "status" && onStatusChange
                        )
                        {
                            onStatusChange(dataExtractedFromJson.data)
                        }
                        else if
                            (dataExtractedFromJson.type === "error") {
                            throw new Error(dataExtractedFromJson.data);
                        }
                        else if (
                            dataExtractedFromJson.type === "final")
                        {
                            streamOutput = dataExtractedFromJson.data;
                        }
                        
                    }
                    catch (parseError)// normalny error jest pod koniec
                    {
                        if(!(parseError instanceof SyntaxError))
                        {
                            throw parseError; //jest to błąd backendu. Ignorujemy
                        }
                        console.warn(
                            "Komunikat: Uszkodzony fragment strumienia LLM zignorowany:",
                            line
                        );
                    }
                    
                }
            }
        }//while

        if (typeof streamOutput === "object" && streamOutput !== null)//LangChain lubi zwracać obiekt, a nie stringa
        {
            return streamOutput.text || JSON.stringify(streamOutput)
        }

        return streamOutput;



    }
    catch (error)
    {
        console.error(
            "Wystąpił błąd podczas wysyświetlania:", error
        );
        throw error; // Rzucamy błąd dalej, aby obsłużyć go w komponencie
    }
};