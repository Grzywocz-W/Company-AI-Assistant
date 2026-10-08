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
import './chatWindow.css';

//pliki
import
{
    AgentCallingStatusEnum
}
    from '../constants/agentCallingStatus';
import
{
    BASE_URL//podstawowy URL PODCZAS TETSOWANIA
}
    from '../constants/config'//teraz jest w config.

export default function ChatWindow()
{
    const [isSessionOnline, setIsSessionOnline] = useState(true);
    const sessionTimer = useRef(null);


    const [userInput, setUserInput] = useState('');
    //const [responseText, setResponseText] = useState('');//chyba niepotrzebne
    const [messagesList, setMessagesList] = useState([]);
    const [isResponding, setIsResponding] = useState(false);//domyślnie nie odpowiada

    const [sessionID, setSessionID] = useState("");

    const [responseStatus, setResponseStatus] = useState("THINKING");

    const [isAdminControl, setIsAdminControl] = useState(false);

    const [hasAdminAccess, setHasAdminAccess] = useState(false);

    const messageEndingRef = useRef(null);

    const [attachedFile, setAttachedFile] = useState(null);//nieobowiązkowe
    const attachedFileRef = useRef(null);



    const [isAdminPanelVisible, setIsAdminPanelVisible] = useState(false);
    const [adminPassword, setAdminPassword] = useState("");

  

    useEffect(
        () =>
    {
        const randSessID = "ses_" + crypto.randomUUID();//potem dodać numerowanie sesji
        setSessionID(randSessID);// podkreśla bo nie generuje losowe treści i taki jest problem

        //najpierw sprawdzamy ip admina, potem timer
        const adminIpVerification = async () =>
        {
            try
            {
                const ipResponse = await fetch(
                    `${BASE_URL}/check-ip`
                );
                const isAdminPrivAllowed = await ipResponse.json();

                if (isAdminPrivAllowed['is-admin-control-allowed'] === true)
                {
                    setIsAdminControl(true);
                }
            }
            catch (error)
            {
                console.error("Nie można sprawdzić adresu IPv4:", error);
            }
        };
        adminIpVerification();


        updateValueSessionTimer();
        return () =>
        {
            if (sessionTimer.current)
            {
                clearTimeout(sessionTimer.current)
            }
        }

        
    },
        []
    );

    useEffect(() =>
    {
        if (messageEndingRef.current)
        {
            messageEndingRef.current.scrollIntoView(
                { behavior: "auto" }
            );
        }
    },
        [messagesList, isResponding, responseStatus],
    )
        ;
    

    const updateValueSessionTimer =
        () =>
        {
            if (sessionTimer.current)
            {
            clearTimeout(sessionTimer.current);
            }

        sessionTimer.current = setTimeout(
            () => {
                setIsSessionOnline(false);
                const expiredMessage =
                {
                    role: 'ai',
                    text: 'Sesja wygasła z powodów bezpieczeństwa bezpieczeństwa. Odśwież stronę i spróbuj ponownie',
                };
                setMessagesList(
                    (prev) => [...prev, expiredMessage]
                );

            },
            1800000
        );
    }


    const handleSend = async () =>
    {
        if (!userInput.trim() || isResponding || !isSessionOnline)//blokada
        {
            return;
        }

        updateValueSessionTimer();//aktualizacja czasu



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
            textInUsersBubble = `Załączono plik: ${fileAttachedToMessage.name}\n${messageContent}`;//informujemy jaki plik został załączony i treść wiadomości
        }

        const newMessageTMP =
        {
            role: 'user',
            text: textInUsersBubble
        }
        setMessagesList(
            (prev) => [...prev, newMessageTMP]
        );//prev, bo jak lista jest w await to cały czas pamięta poprzednią wersje


        setIsResponding(true);

        setResponseStatus("THINKING");

        try
        {
            //w osobnym pliku
            const result = await sendTextToFastAPI(
                messageContent,
                sessionID,
                fileAttachedToMessage,
                hasAdminAccess,
                (newStatus) => {
                    setResponseStatus(newStatus)
                }//callback z serwera. Przychodzi paczka: z onStatusChange(dataFromJson.data)
            );

            const newMessageTMP =
            {
                role: 'ai', text: result
            }
            setMessagesList(
                (prev) => [...prev, newMessageTMP]
            );

            
        }
        catch (error)
        {
            console.error("ERROR:", error);//error
            const newMessageTMP = {
                role: 'ai',
                text: 'Błąd komunikacji z LLM'
            }
            setMessagesList(
                (prev) => [...prev, newMessageTMP]
            );
            
        }

        setIsResponding(false);
    };


    //napis na pasku wiadomości
    let inputBarMessage = "";

    if (isSessionOnline)
    {
        inputBarMessage = "Zapytaj agenta ...";
    }
    else
    {
        inputBarMessage = "Sesja wygasła. Proszę odśwież stronę.";
    }

    const handleAdminLogin = async () =>
    {
        if ( !adminPassword.trim() )
        {
            return;
        }
        //testuje zapytanie
        try
        {
            const response = await fetch(`${BASE_URL}/admin-login`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(
                    {
                    password: adminPassword,
                    sessionID: sessionID
                    }
                )
            });

            const loginData = await response.json()

            if (loginData.status === "correct")
            {
                setHasAdminAccess(true);
                console.log("Poprawnie zalogowano na administratora")

            }
            else
            {
                console.log("NNiepoprawnie zalogowane na administratora. Sprawdź backend")
            }



        }
        catch(error)
        {
            console.error(
                "Nieznany i nieobsługiwany wyjątek, który wystąpił podczas logowania",
                error
            )
        }


        //czyścimy okienko
        setAdminPassword('');
        setIsAdminPanelVisible(false);
    };


    const handleAdminLogout = async () => {
        try {
            const response = await fetch(
                `${BASE_URL}/admin-logout`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(
                        {
                        sessionID: sessionID
                        }
                    )
                }
            );

        }
        catch (error)
        {
            console.error("Błąd przy wylogowywaniu", error)
        }


        //Należy wyczyścić okno po zalogowaniu, aby system tego nie pamiętał
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
                <div className="admin_Header">
                    {!hasAdminAccess ?
                        (
                        <button
                            className="adminLoginButton"
                                onClick={
                                    () => setIsAdminPanelVisible(true)
                                }
                            title="Zaloguj się do administratora"
                        >
                            ⚙️
                        </button>
                
                    ) : (
                        <button
                            className="adminLogoutButton"
                                onClick={
                                    handleAdminLogout
                                }
                            title="Wyloguj się konta Admina"
                                style=
                                {
                                    {
                                        fontSize: '1.2rem',
                                        background: 'transparent',
                                        cursor: 'pointer',
                                        border: 'none',
                                    }
                                }
                        >
                            🔓
                        </button>
                )
                }
                </div>   
                )
            }


            {/*okno logowania*/ }
            {isAdminPanelVisible &&
                (
                <div className="adminPanelWindow">
                    <div className="adminPanelWindowPage">
                        <h3>🔒 Dostęp do panelu logowania</h3>
                        <p>Podaj hasło:</p>
                        <input
                            type="password"
                            value=
                            {
                                adminPassword
                            }
                            onChange={
                                (e) => setAdminPassword(e.target.value)
                            }
                            onKeyDown={
                                (e) => e.key === 'Enter' && handleAdminLogin()
                            }
                            autoFocus
                        />
                        <div className="adminPanelWindowButtons">
                            <button className="exitBtn" onClick={() =>
                            {
                                setIsAdminPanelVisible(false);
                                setAdminPassword('');
                            }
                            }
                            >Anuluj
                            </button>
                            <button className="loginBtn"
                                onClick={handleAdminLogin
                                }
                            >
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
                {/* Okno z eksploratorem plikow*/}
                <input
                    type="file"
                    accept=".pdf"
                    ref={
                        attachedFileRef
                    }
                    className="fileExplorerWindow"
                    onChange={
                        (e) => setAttachedFile(e.target.files[0])
                    }
                />

                {/* Przycisk spinacza*/}
                <button
                    onClick={
                        () => attachedFileRef.current.click()
                    }
                    disabled={isResponding || !isSessionOnline}
                    className="paperClipButton"
                    title="Załącz plik PDF"
                >
                    📎
                </button>
                <input
                    type="text"
                    value=
                    {
                        userInput
                    }
                    onChange=
                    {
                        (e) => setUserInput(e.target.value)
                    }
                    onKeyDown=
                    {
                        (e) => e.key === 'Enter' && handleSend()
                    } //Enter
                    placeholder=
                    {
                        inputBarMessage
                    }
                    disabled=
                    {
                        isResponding || !isSessionOnline
                    } //Blokada jak myśli lub out of sesji
                />

                <button
                    onClick=
                    {
                        handleSend
                    }
                    disabled=
                    {
                        isResponding || !userInput.trim() || !isSessionOnline
                    }
                >
                    Wyślij
                </button>
            </div>

        </div>
    );
}