//chatWindows.jsx
import {
    useState,
    useEffect,
    useRef,
} from 'react';

import ReactMarkdown from 'react-markdown';

import {
    sendTextToFastAPI
} from '../api/fastApiConnector';
import './ChatWindow.css';
import { AgentCallingStatusEnum } from '../constants/agentCallingStatus';

export default function TextInput() {
    const [userInput, setUserInput] = useState('');
    //const [responseText, setResponseText] = useState('');//chyba niepotrzebne
    const [messagesList, setMessagesList] = useState([]);
    const [isResponsing, setIsResponsing] = useState(false);//domyślnie nie odpowiada

    const [sessionID, setSessionID] = useState("");

    const [isSessionOnline, setIsSessionOnline] = useState(true);
    const sessionTimer = useRef(null);

    const [attachedFile, setAttachedFile] = useState(null);//nieobowiązkowe
    const attachedFileRef = useRef(null);

    const [responseStatus, setResponseStatus] = useState("THINKING");

    const updateSessionTime = () =>
    {
        if (sessionTimer.current)
        {
            clearTimeout(sessionTimer.current);
        }

        sessionTimer.current = setTimeout(() => {
            setIsSessionOnline(false);
            const expiredMessage =
            {
                role: 'ai',
                text: 'Sesja wygasłą ze względu bezpieczeństwa. Spróbuj ponownie',
            };
            setMessagesList((prev) => [...prev, expiredMessage]);

        }, 1800000);
    }

    useEffect(() =>
    {
        const randSessID = "ses_" + crypto.randomUUID();;//potem dodać numerowanie sesji
        setSessionID(randSessID);// podkreśla bo nie generuje losowe treści i taki jest problem


        updateSessionTime();
        return () =>
        {
            if (sessionTimer.current)
            {
                clearTimeout(sessionTimer.current)
            }
        }
    },[]
    );

    const handleSend = async () =>
    {
        if (!userInput.trim() || isResponsing || !isSessionOnline)//blokada
        {
            return;
        }

        updateSessionTime();//aktualizacja czasu



        const fileAttachedToMessage = attachedFile;
        const messageContent = userInput;


        setUserInput('');
        setAttachedFile(null)//opróżnij plik
        if (attachedFileRef.current)
        {
            attachedFileRef.current.value = '';
        }

        let textInUsersBubble = messageContent;
        if (fileAttachedToMessage)
        {
            textInUsersBubble = `Załączono plik: ${fileAttachedToMessage.name}\n${messageContent}`;
        }

        const newMessageTMP = { role: 'user', text: textInUsersBubble }
        setMessagesList((prev) => [...prev, newMessageTMP]);//prev, bo jak lista jest w await to cały czas pamięta poprzednią wersje


        setIsResponsing(true);

        setResponseStatus("THINKING");

        try
        {
            //wosobnym pliku
            const result = await sendTextToFastAPI(
                messageContent,
                sessionID,
                fileAttachedToMessage,
                (newStatus) => { setResponseStatus(newStatus) }//callback z serwera. Przychodzi paczka: z onStatusChange(dataFromJson.data)
            );

            const newMessageTMP = {role: 'ai', text: result}
            setMessagesList((prev)=>[...prev, newMessageTMP]);

            
        }
        catch (error)
        {
            console.error("ERROR:", error);//error
            const newMessageTMP = { role: 'ai', text: 'Błąd komunikacji z LLM' }
            setMessagesList((prev) => [...prev, newMessageTMP]);
            
        }

        setIsResponsing(false);
    };


    //napis na pasku wiadomości
    let inputBarMessage = "";

    if (isSessionOnline) {
        inputBarMessage = "Zapytaj agenta...";
    }
    else
    {
        inputBarMessage = "Sesja wygasła. Odśwież stronę.";
    }

    return (
        <div className="chatWindow">

            {/* Główne okno z historią */}
            <div className="chatHistory">
                {messagesList.map((msg, index) =>
                (
                    <div key={index} className={`messageRow ${msg.role}`}>
                        <div className={`messageBubble ${msg.role}`}>
                            <ReactMarkdown>{msg.text}</ReactMarkdown>
                        </div>
                    </div>
                )
                )
                }

                {/* Pobiera info ze zmiennej co robi */}
                {isResponsing && (
                    <div className="messageRow ai">
                        <div className="messageBubble ai">
                            {AgentCallingStatusEnum[responseStatus] || AgentCallingStatusEnum.THINKING}
                        </div>
                    </div>
                )}
            </div>

            {/*Pasek z podglądem wybranego pliku nad polem wpisywania */}
            {attachedFile &&
                (
                <div className = "fileAttachButton">
                    <span>
                        📎 Wybrano plik: <strong>{attachedFile.name}</strong>
                    </span>
                    <button
                        className="attachedFileRemoveButton"
                        onClick={() =>
                        {
                            setAttachedFile(null);
                            if (attachedFileRef.current)
                            {
                                attachedFileRef.current.value = '';
                            } // <--- ZMIENIONY onClick
                        }}
                       
                        title="Usuń załącznik"
 /*to jest od buttona*/>
                        X
                    </button>
                </div>
            )}

            {/* Dolny pasek z przyciskiem */}


            <div className="chatInputBar">
                {/* Okno z ekploatorem plikow*/}
                <input
                    type="file"
                    accept=".pdf"
                    ref={attachedFileRef}
                    className="fileExplolerWindow"
                    onChange={(e) => setAttachedFile(e.target.files[0])}
                />

                {/* Przycisk spinacza*/}
                <button
                    onClick={() => attachedFileRef.current.click()}
                    disabled={isResponsing || !isSessionOnline}
                    className="paperClipButton"
                    title="Załącz plik PDF"
                >
                    📎
                </button>
                <input
                    type="text"
                    value={userInput}
                    onChange={(e) => setUserInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSend()} //Enter
                    placeholder={inputBarMessage}
                    disabled={isResponsing || !isSessionOnline} //Blokada jak myśli lub out of sesji
                />

                <button onClick={handleSend} disabled={isResponsing || !userInput.trim() || !isSessionOnline}>
                    Wyślij
                </button>
            </div>

        </div>
    );
}