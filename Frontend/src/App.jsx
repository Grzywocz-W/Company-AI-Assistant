import {
    useState,
    useEffect
} from 'react'
import './App.css'

import ChatWindow from './components/chatWindow'

const TIP_APPERANCE_DURATION_MS = 5000



const TIPS_TEXT = [
    'Nie wiesz co robić? Zapytaj asystenta o regulamin sklepu: zwroty, reklamacje, czas dostawy.',
    'Pytaj śmiało o asortyment, wbudowany asystent od razu Ci odpowie.',
    'Możesz załączyć PDF (np. fakturę), a asystent Ci ją omówi i pokieruje Cię dalej.',
    'Zapytaj o status Twojego zamówienia, podając jego numer, np. ZA-2026-1001.',
]




const SYSTEM_STATUSES = [
    {
        icon: '',
        name: 'Myślę',
        desc: 'System agentowy analizuje Twoje zapytanie'
    },
    {
        icon: '',
        name: 'Szukam w Internecie',
        desc: 'System agentowy szuka dodatkowych informacji w sieci internetowej z poszanowaniem Twojej anonimowości'
    },
    {
        icon: '',
        name: 'Przeszukuję dokumenty',
        desc: 'System agentowy odpytuje wektorową bazę, analizuje regulamin i dzięki systemowi RAG zwraca poprawną odpowiedź'
    },
    {
        icon: '️',
        name: 'Sprawdzam w bazie danych',
        desc: 'System agentowy przeszukuje firmową bazę danych, aby udzielić Ci najlepszych odpowiedzi'
    },
]


const INSTRUCTION_STEPS = [
    {
        title: 'Wpisz zapytanie',
        text: 'Wykorzystaj pole tekstowe na dole czatu. Zatwierdź je za pomocą przycisku „Wyślij” albo klawiszem Enter.',
    },
    {
        title: 'Coś nie działa?',
        text: 'Stosuj się do komunikatów w czacie. W ostateczności odśwież stronę.',
    },
    {
        title: 'Załącz plik PDF (Opcjonalnie)',
        text: 'Naciśnij przycisk spinacza po lewej stronie okna tekstowego, aby przekazać jeden dokument do analizy.',
    },
]

function App() {


    const [openInfoStep, setOpenInfoStep] = useState(0)
    const [infoTipIndex, setInfoTipIndex] = useState(0)





    useEffect(() => {
        const infoTipsStayDurationTimer = setInterval(nextInfoTip, TIP_APPERANCE_DURATION_MS)

        function stopInfoTipsTimer() {
            clearInterval(infoTipsStayDurationTimer)
        }
        function nextInfoTipIdxGetter(currIdx) {
            if (currIdx + 1 >= TIPS_TEXT.length) {
                return 0
            }
            else {
                return currIdx + 1
            }
        }

        function nextInfoTip() {
            setInfoTipIndex(nextInfoTipIdxGetter)
        }

        return stopInfoTipsTimer
    },

        [])





    function turnInfoStep(idx) {
        if (openInfoStep === idx) {
            setOpenInfoStep(-1)
        }
        else { setOpenInfoStep(idx) }
    }

    function stepClassNameGetter(idx) {
        if (openInfoStep === idx) {
            return 'infoStep open'
        }
        return 'infoStep'
    }

    function tipCircleClassNameGetter(idx) {
        if (infoTipIndex === idx) {
            return 'tipCircle active'
        }
        else {
            return 'tipCircle'
        }
    }


    function ulRenderInfoStep(step, stepIdx) {
        function handleInfoStepClick() {
            turnInfoStep(stepIdx)
        }

        return (
            <li key={stepIdx} className={stepClassNameGetter(stepIdx)}>
                <button className="infoStepHead"
                    onClick={handleInfoStepClick
                    }>
                    <span className="infoStepNum">{stepIdx + 1}</span>
                    {step.title}
                    <span className="infoStepArrow">▾</span>
                </button>
                <div className="infoStepBody">{step.text}</div>
            </li>


        )

    }

    function generateTipsCircle(_, tipIdx) {/*_ to treść, nie interesuje nas ona, na razie */
        return (
            <span key={tipIdx} className={tipCircleClassNameGetter(tipIdx)} />
        )
    }

    function ulGenerateSystemStatusField(agentStatus) {
        return (
            <li key={agentStatus.name}>
                <span className="legendIcon">{agentStatus.icon}</span>
                <span>{agentStatus.name}<small>{agentStatus.desc}</small></span>
            </li>
        )

    }


    return (
        <>

            {/* animowane tło */}
            <div className="backgorudAnimated" aria-hidden="true">
                <div className="gridPattern" />
                <div className="glowingCircle topLeftCorner" />
                <div className="glowingCircle bottomRightCorner" />
                <div className="glowingCircle centering" />
            </div>

            <div className="app">
                {/* nagłówek */}


                <header className="appHeader">
                    <div className="icon">
                        <div className="iconLogo">AI</div>
                        <div>
                            <div className="iconName">COMPANY<span>-AI</span></div>
                            <div className="iconSub">Inteligentny asystent sklepu internetowego</div>
                        </div>
                    </div>
                    <div className="headerRight">
                        <a className="gitHubLink" href="https://github.com/"
                            target="_blank" rel="noopener noreferrer">GitHub ↗</a>
                    </div>
                </header>

                <main className="layout">
                    {/* LEWA KOLUMNA – instrukcja */}
                    <aside className="sideCol">
                        <section className="uiPanel">
                            <h2 className="uiPanelTitle"> Instrukcja obsługi</h2>
                            <p className="uiPanelSub"></p>
                            <ul className="instructionSteps">
                                {INSTRUCTION_STEPS.map(ulRenderInfoStep)}
                            </ul>
                        </section>
                    </aside>

                    {/* ŚRODEK – czat (bez zmian) */}
                    <div className="chatWindowArea">
                        <ChatWindow />
                    </div>

                    {/* PRAWA KOLUMNA – widgety */}
                    <aside className="sideCol right">

                        <section className="uiPanel">
                            <h2 className="uiPanelTitle">Co robi asystent?</h2>
                            <p className="uiPanelSub">Stany, które są widoczne podczas odpowiedzi</p>
                            <ul className="legend">
                                {SYSTEM_STATUSES.map(ulGenerateSystemStatusField)}
                            </ul>
                        </section>



                        <section className="uiPanel">
                            <h2 className="uiPanelTitle"> Wskazówka</h2>
                            <p className="tipText" key={infoTipIndex}>{TIPS_TEXT[infoTipIndex]}</p>
                            <div className="tipCircles">
                                {TIPS_TEXT.map(generateTipsCircle)}
                            </div>
                        </section>


                    </aside>
                </main>



                <footer className="appFooter">
                    <div>Praca inżynierska · Specjalistyczny asystent z integracją LLM i sieci neuronowej</div>
                    <div className="footerAuthors">
                        <span className="authorPill">Michał Tarnawa</span>
                        <span className="authorPill">Wojciech Grzywocz</span>
                    </div>
                </footer>
            </div>
        </>
    )
}

export default App