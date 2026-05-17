//fastApiConnector

export const sendTextToFastAPI = async (text, sessionID, attachedFile = null, isAdmin = false, onStatusChange = null) =>
{
    const requestDataForm = new FormData();//aby dodaæ pdf'a trzeba stworzyæ forma

    //nazwy pól musz¹ siê zgadzaæ z tym co jest w main.py
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
            //przegl¹darka powinna sobie poradziæ bez tego
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
            throw new Error('B³¹d sieci z FastAPI');
        }

        const toolCallingStreamReader = response.body.getReader();//odczyt kawa³ek po kawa³ku
        const textDeconder = new TextDecoder();//dane to surowe bajty

        let streamBuffer = '';
        let streamOutput = '';

        while (true)//dzia³a tak d³ugo, a¿ stream siê nie zakoñczy
        {           //nazwy te s¹ zdefiniowane przez reacta
            const { done, value } = await toolCallingStreamReader.read();//czeka na wywo³anie narzêdzia

            if (done)
            {
                break;
            }


            streamBuffer = streamBuffer + textDeconder.decode(value, { stream: true });

            const lines = streamBuffer.split('\n');

            streamBuffer = lines.pop();//ostatnielinijka mo¿e nie byæ pe³na

            for (const line of lines)// of nie in
            {
                if (line.trim() != '')//wyci¹gamy wartoœci z pól
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
                            throw parseError; //jest to b³¹d backedu. Ignorujemy
                        }
                        console.warn("Uszkodzony fragment strumieniaLLM Zignorowany:", line);
                    }
                    
                }
            }
        }//while

        if (typeof streamOutput === "object" && streamOutput !== null)//LangChain lubi zwracaæ obiekt, a nie stringa
        {
            return streamOutput.text || JSON.stringify(streamOutput)
        }

        return streamOutput;

        //const data = await response.json();
        ////return data.result;
        //if (typeof data.result === "object" && data.result !== null)// przez LangChaina Python zwraca signature odpowiedzi, wiêc doda³em zabezpiecznie. Uwa¿aj Wojtek.
        //{
        //    return data.result.text || JSON.stringify(data.result)
        //}

        //return data.result;

    }
    catch (error)
    {
        console.error("Wyst¹pi³ b³¹d podczas wysy³ania:", error);
        throw error; // Rzucamy b³¹d dalej, aby obs³u¿yæ go w komponencie
    }
};