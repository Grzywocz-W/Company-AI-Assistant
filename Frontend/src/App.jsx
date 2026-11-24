import { useState, useEffect } from 'react'
import './App.css'

import ChatWindow from './components/chatWindow'

const STEPS = [
    {
        title: 'Wpisz zapytanie',
        text: 'Użyj pola na dole czatu. Wyślij przyciskiem „Wyślij” albo klawiszem Enter.',
    },
    {
        title: '(Opcjonalnie) Załącz plik PDF',
        text: 'Kliknij spinacz obok pola tekstowego, aby przesłać dokument do analizy. Można załączyć tylko jeden plik PDF.',
    },
    {
        title: 'Coś nie działa?',
        text: 'Stosuj się do komunikatów w czacie. Po wygaśnięciu sesji odśwież stronę, aby zacząć nową rozmowę.',
    },
]

const AGENT_STATES = [
    { icon: '🧠', name: 'Myślę', desc: 'Agent Koordynator analizuje zapytanie' },
    { icon: '🗄️', name: 'Sprawdzam w bazie danych', desc: 'Agent przeszukuję naszą firmową bazę danych w celu udzielenia Ci lepszych odpowiedzi' },
    { icon: '📄', name: 'Przeszukuję dokumenty', desc: 'Agent analizuje regulamin i politykę, aby przekazać ci aktualne informacje' },
    { icon: '🌐', name: 'Szukam w Internecie', desc: 'Agent anonimowo wyszukuje dodatkowych informacji na stronach internetowych' },
]

const TIPS = [
    'Zapytaj o status zamówienia, podając jego numer, np. ZA-2026-1001.',
    'Możesz zapytać o regulamin sklepu: zwroty, reklamacje, czas dostawy.',
    'Załącz PDF (np. fakturę) i poproś asystenta o jej omówienie.',
    'Pytaj śmiało o nasz asortyment, nasz asystent AI od razu udzieli Ci odpowiedzi.',
]

function App() {
    const [showNotice, setShowNotice] = useState(true)
    const [openStep, setOpenStep] = useState(0)
    const [now, setNow] = useState(new Date())
    const [tipIndex, setTipIndex] = useState(0)

    useEffect(() => {
        const clock = setInterval(() => setNow(new Date()), 1000)
        const tips = setInterval(() => setTipIndex((i) => (i + 1) % TIPS.length), 8000)
        return () => {
            clearInterval(clock)
            clearInterval(tips)
        }
    }, [])

    const timeText = now.toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    const dateText = now.toLocaleDateString('pl-PL', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })

    return (
        <>
            {/* animowane tło */}
            <div className="appBg" aria-hidden="true">
                <div className="grid" />
                <div className="blob b1" />
                <div className="blob b2" />
                <div className="blob b3" />
            </div>

            <div className="app">
                {/* nagłówek */}
                <header className="appHeader">
                    <div className="brand">
                        <div className="brandLogo">AI</div>
                        <div>
                            <div className="brandName">COMPANY<span>-AI</span></div>
                            <div className="brandSub">Inteligentny asystent sklepu internetowego</div>
                        </div>
                    </div>
                    <div className="headerRight">
                        <div className="onlinePill">
                            <span className="onlineDot" /> System online
                        </div>
                        <a className="ghLink" href="https://github.com/"
                            target="_blank" rel="noopener noreferrer">GitHub ↗</a>
                    </div>
                </header>

                {/* informacja dnia (zamykana) */}
                {showNotice && (
                    <div className="noticeBar" role="status">
                        <span className="noticeIcon">💡</span>
                        <div className="noticeText">
                            <strong>Informacja dnia:</strong> W naszym sklepie JUŻ TERAZ możesz zadać pytanie wirtualnemu asystentowi, który korzysta z firmowej bazy danych, regulaminu sklepu
                            oraz wyszukiwarki, aby świadczyć jak najlepszą jakość odpowiedzi i nieść natychmiastową pomoc naszym klientom.
                        </div>
                        <button className="noticeClose" onClick={() => setShowNotice(false)}
                            aria-label="Zamknij informację">✕</button>
                    </div>
                )}

                <main className="layout">
                    {/* LEWA KOLUMNA – instrukcja */}
                    <aside className="sideCol">
                        <section className="card">
                            <h2 className="cardTitle">📘 Instrukcja obsługi</h2>
                            <p className="cardSub"></p>
                            <ul className="steps">
                                {STEPS.map((s, i) => (
                                    <li key={i} className={`step ${openStep === i ? 'open' : ''}`}>
                                        <button className="stepHead"
                                            onClick={() => setOpenStep(openStep === i ? -1 : i)}>
                                            <span className="stepNum">{i + 1}</span>
                                            {s.title}
                                            <span className="stepArrow">▾</span>
                                        </button>
                                        <div className="stepBody">{s.text}</div>
                                    </li>
                                ))}
                            </ul>
                        </section>

                        <section className="card">
                            <h2 className="cardTitle">🕒 Teraz</h2>
                            <div className="clockTime">{timeText}</div>
                            <div className="clockDate">{dateText}</div>
                        </section>
                    </aside>

                    {/* ŚRODEK – czat (bez zmian) */}
                    <div className="chatSlot">
                        <ChatWindow />
                    </div>

                    {/* PRAWA KOLUMNA – widgety */}
                    <aside className="sideCol right">
                        <section className="card">
                            <h2 className="cardTitle">🤖 Co robi asystent?</h2>
                            <p className="cardSub">Statusy widoczne podczas odpowiedzi</p>
                            <ul className="legend">
                                {AGENT_STATES.map((a) => (
                                    <li key={a.name}>
                                        <span className="legendIcon">{a.icon}</span>
                                        <span>{a.name}<small>{a.desc}</small></span>
                                    </li>
                                ))}
                            </ul>
                        </section>

                        <section className="card">
                            <h2 className="cardTitle">✨ Wskazówka</h2>
                            <p className="tipText" key={tipIndex}>{TIPS[tipIndex]}</p>
                            <div className="tipDots">
                                {TIPS.map((_, i) => (
                                    <span key={i} className={`tipDot ${i === tipIndex ? 'active' : ''}`} />
                                ))}
                            </div>
                        </section>
                    </aside>
                </main>

                <footer className="appFooter">
                    <div>Praca inżynierska · Specjalistyczny asystent z integracją LLM i sieci neuronowej</div>
                    <div className="footerAuthors">
                        <span className="authorChip">Michał Tarnawa</span>
                        <span className="authorChip">Wojciech Grzywocz</span>
                    </div>
                </footer>
            </div>
        </>
    )
}

export default App