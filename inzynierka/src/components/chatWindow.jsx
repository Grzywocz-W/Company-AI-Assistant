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

export default function ChatWindow() {
    const [userInput, setUserInput] = useState('');
    //const [responseText, setResponseText] = useState('');//chyba niepotrzebne
    const [messagesList, setMessagesList] = useState([]);
    const [isResponding, setIsResponding] = useState(false);//domyślnie nie odpowiada

    const [sessionID, setSessionID] = useState("");

    const [isSessionOnline, setIsSessionOnline] = useState(true);
    const sessionTimer = useRef(null);

    const [attachedFile, setAttachedFile] = useState(null);//nieobowiązkowe
    const attachedFileRef = useRef(null);

    const [responseStatus, setResponseStatus] = useState("THINKING");

    const [isAdminControl, setIsAdminControl] = useState(false);

    const [isAdminPanelVisible, setIsAdminPanelVisible] = useState(false);
    const [adminPassword, setAdminPassword] = useState("");
    const [hasAdminAccess, setHasAdminAccess] = useState(false);

    const messageEndingRef = useRef(null);

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

        //najpierw sprawdzamy ip admina, potem timer
        const adminIpVerification = async () => {
            try {
                const ipResponse = await fetch('http://127.0.0.1:8000/check-ip');
                const isAdminPrivAllowed = await ipResponse.json();

                if (isAdminPrivAllowed['is-admin-control-allowed'] === true) {
                    setIsAdminControl(true);
                }
            }
            catch (error) {
                console.error("Nie da się sprawdzić IP:", error);
            }
        };
        adminIpVerification();


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

    useEffect(() =>
    {
        if (messageEndingRef.current)
        {
            messageEndingRef.current.scrollIntoView({ behavior: "smooth" });
        }
    },
        [messagesList, isResponding, responseStatus],)
        ;
    

    const handleSend = async () =>
    {
        if (!userInput.trim() || isResponding || !isSessionOnline)//blokada
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


        setIsResponding(true);

        setResponseStatus("THINKING");

        try
        {
            //wosobnym pliku
            const result = await sendTextToFastAPI(
                messageContent,
                sessionID,
                fileAttachedToMessage,
                hasAdminAccess,
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

        setIsResponding(false);
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

    const handleAdminLogin = async () => {
        if (!adminPassword.trim())
        {
            return;
        }

        try
        {
            const response = await fetch('http://127.0.0.1:8000/admin-login',
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    password: adminPassword,
                    sessionID: sessionID
                })
            });

            const loginData = await response.json()

            if (loginData.status === "correct") {
                setHasAdminAccess(true);
                console.log("Logowanie na admina")

            }
            else
            {
                console.log("Niepoprawna próba logowania na admina")
            }



        }
        catch(error)
        {
            console.error("Błąd przy logowania", error)
        }


        //czyścimy okienko
        setAdminPassword('');
        setIsAdminPanelVisible(false);
    };


    const handleAdminLogout = async () => {
        try {
            const response = await fetch('http://127.0.0.1:8000/admin-logout',
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        sessionID: sessionID
                    })
                });

        }
        catch (error) {
            console.error("Błąd przy wylogowywaniu", error)
        }


        //czyścimy okienko
        setHasAdminAccess(false);
        setAdminPassword('');
        setIsAdminPanelVisible(false);
    };

    return (
        /*<div className="chatWindow">*/
        <div className={`chatWindow ${hasAdminAccess ? 'masterMode' : ''}`}>
            {/*panel admina*/ }

            {isAdminControl &&
                (
                <div className="adminHeader">
                    {!hasAdminAccess ? (
                        <button
                            className="adminLoginButton"
                            onClick={() => setIsAdminPanelVisible(true)}
                            title="Admin Login Panel"
                        >
                            ⚙️
                        </button>
                
                    ) : (
                        <button
                            className="adminLogoutButton"
                            onClick={handleAdminLogout}
                            title="Wyloguj z panelu Admina"
                            style={{ background: 'transparent', border: 'none', cursor: 'pointer', fontSize: '1.2rem' }}
                        >
                            🔓
                        </button>
                )
                }
                </div>   
            )}


            {/*okno logowania*/ }
            {isAdminPanelVisible &&
                (
                <div className="adminPanelWindow">
                    <div className="adminPanelWindowPage">
                        <h3>🔒 Dostęp do panelu logowania</h3>
                        <p>Podaj hasło:</p>
                        <input
                            type="password"
                            value={adminPassword}
                            onChange={(e) => setAdminPassword(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleAdminLogin()}
                            autoFocus
                        />
                        <div className="adminPanelWindowButtons">
                            <button className="exitBtn" onClick={() =>
                            {
                                setIsAdminPanelVisible(false);
                                setAdminPassword('');
                            }
                            }>Anuluj
                            </button>
                            <button className="loginBtn" onClick={handleAdminLogin}>
                                Zaloguj
                            </button>
                        </div>
                    </div>
                </div>
            )}

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
                {isResponding && (
                    <div className="messageRow ai">
                        <div className="messageBubble ai thinking">
                            {AgentCallingStatusEnum[responseStatus] || AgentCallingStatusEnum.THINKING}
                        </div>
                    </div>
                )}
                <div ref={messageEndingRef} />
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
                    disabled={isResponding || !isSessionOnline}
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
                    disabled={isResponding || !isSessionOnline} //Blokada jak myśli lub out of sesji
                />

                <button onClick={handleSend} disabled={isResponding || !userInput.trim() || !isSessionOnline}>
                    Wyślij
                </button>
            </div>

        </div>
    );
}