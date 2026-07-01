//fastApiConnector

export const sendTextToFastAPI = async (text, sessionID, attachedFile = null, isAdmin = false, onStatusChange = null) =>
{
    const requestDataForm = new FormData();//aby doda� pdf'a trzeba stworzy� forma

    //nazwy p�l musz� si� zgadza� z tym co jest w main.py
    requestDataForm.append('sessionID', sessionID);
    requestDataForm.append('request', text);

    requestDataForm.append('isAdmin', isAdmin);


    if (attachedFile)
    {
        requestDataForm.append('attachedFile', attachedFile)
    }


    try {
        const response = await fetch('http://127.0.0.1:8000/chat', {
            method: 'POST',
            //przegl�darka powinna sobie poradzi� bez tego
            //headers: {
            //    'Content-Type': 'application/json',
            //},
            //body: JSON.stringify(
            //    {
            //        sessionID: sessionID,
            //        text: text,
            //    }
            //),
            body: requestDataForm
        });

        if (!response.ok) {
            throw new Error('Błąd sieci z FastAPI');
        }

        const toolCallingStreamReader = response.body.getReader();//odczyt kawa�ek po kawa�ku
        const textDecoder = new TextDecoder();//dane to surowe bajty

        let streamBuffer = '';
        let streamOutput = '';

        while (true)//dzia�a tak d�ugo, a� stream si� nie zako�czy
        {           //nazwy te s� zdefiniowane przez reacta
            const { done, value } = await toolCallingStreamReader.read();//czeka na wywo�anie narz�dzia

            if (done)
            {
                break;
            }


            streamBuffer = streamBuffer + textDecoder.decode(value, { stream: true });

            const lines = streamBuffer.split('\n');

            streamBuffer = lines.pop();//ostatnia linijka mo�e nie by� pe�na

            for (const line of lines)// of nie in
            {
                if (line.trim() != '')//wyci�gamy warto�ci z p�l
                {
                    try
                    {
                        const dataFromJson = JSON.parse(line);

                        if (dataFromJson.type === "status" && onStatusChange) {
                            onStatusChange(dataFromJson.data)
                        }
                        else if (dataFromJson.type === "final") {
                            streamOutput = dataFromJson.data;
                        }
                        else if (dataFromJson.type === "error") {
                            throw new Error(dataFromJson.data);
                        }
                    }
                    catch (parseError)// normalny error jest pod koniec
                    {
                        if(!(parseError instanceof SyntaxError))
                        {
                            throw parseError; //jest to b��d backendu. Ignorujemy
                        }
                        console.warn("Uszkodzony fragment strumienia LLM zignorowany:", line);
                    }
                    
                }
            }
        }//while

        if (typeof streamOutput === "object" && streamOutput !== null)//LangChain lubi zwraca� obiekt, a nie stringa
        {
            return streamOutput.text || JSON.stringify(streamOutput)
        }

        return streamOutput;

        //const data = await response.json();
        ////return data.result;
        //if (typeof data.result === "object" && data.result !== null)// przez LangChaina Python zwraca signature odpowiedzi, wi�c doda�em zabezpiecznie. Uwa�aj Wojtek.
        //{
        //    return data.result.text || JSON.stringify(data.result)
        //}

        //return data.result;

    }
    catch (error)
    {
        console.error("Wystąpił błąd podczas wysyświetlania:", error);
        throw error; // Rzucamy b��d dalej, aby obs�u�y� go w komponencie
    }
};