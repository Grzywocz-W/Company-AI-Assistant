//chatWindows.jsx
import { useState } from 'react';
import { sendTextToFastAPI } from '../api/fastApiConnector';

export default function TextInput() {
    const [inputText, setInputText] = useState('');
    const [responseText, setResponseText] = useState('');

    const handleSend = async () => {
        try {
            // Wywołujemy funkcję z naszego osobnego pliku JS
            const result = await sendTextToFastAPI(inputText);
            setResponseText(result);
        } catch (error) {
            setResponseText("Błąd połączenia z serwerem!");
        }
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', alignItems: 'center', marginTop: '20px' }}>
            <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Wpisz coś..."
                style={{ padding: '10px', fontSize: '16px', borderRadius: '8px', border: '1px solid #ccc' }}
            />
            <button className="counter" onClick={handleSend}>
                Wyślij do Pythona
            </button>
            {responseText && (
                <p style={{ marginTop: '15px', fontWeight: 'bold', color: '#646cff' }}>
                    Odpowiedź z FastAPI: {responseText}
                </p>
            )}
        </div>
    );
}