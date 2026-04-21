//fastApiConnector

export const sendTextToFastAPI = async (text) => {
    try {
        const response = await fetch('http://127.0.0.1:8000/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text }),
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