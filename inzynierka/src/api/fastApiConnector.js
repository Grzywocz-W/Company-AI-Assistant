//fastApiConnector

export const sendTextToFastAPI = async (text, sessionID, attachedFile = null) =>
{
    const requestDataForm = new FormData();//aby dodaæ pdf'a trzeba stworzyæ forma

    //nazwy pól musz¹ siê zgadzaæ z tym co jest w main.py
    requestDataForm.append('sessionID', sessionID);
    requestDataForm.append('request', text);
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

        const data = await response.json();
        //return data.result;
        if (typeof data.result === "object" && data.result !== null)// przez LangChaina Python zwraca signature odpowiedzi, wiêc doda³em zabezpiecznie. Uwa¿aj Wojtek.
        {
            return data.result.text || JSON.stringify(data.result)
        }

        return data.result;

    } catch (error) {
        console.error("Wyst¹pi³ b³¹d podczas wysy³ania:", error);
        throw error; // Rzucamy b³¹d dalej, aby obs³u¿yæ go w komponencie
    }
};