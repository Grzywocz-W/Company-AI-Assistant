import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from './assets/vite.svg'
//import heroImg from './assets/hero.png'
import './App.css'

import ChatWindow from './components/chatWindow'
function App() {
  //const [count, setCount] = useState(0)

  return (
      <>{/*
      <section id="center">
        <div className="hero">
          <img src={heroImg} className="base" width="170" height="179" alt="" />
          <img src={reactLogo} className="framework" alt="React logo" />
          <img src={viteLogo} className="vite" alt="Vite logo" />
        </div>
        <div>
          <h1>Get started</h1>
          <p>
            Edit <code>src/App.jsx</code> Witaj świecie <code>HMR</code>
          </p>
        </div>
        <button
          className="counter"
          onClick={() => setCount((count) => count + 1)}
        >
          Count is {count}
        </button>
          </section>*/}

          <section id="left-side-bar">
             <svg className="icon" role="presentation" aria-hidden="true">
                  <use href="/icons.svg#documentation-icon"></use>
              </svg>

              <h2>Instruckja obsługi</h2>
              <p>Skrócona wersja</p>
              <ul>
                  <li>
                      <a href="https://vite.dev/" target="_blank" rel="noopener noreferrer">
                          1. Wpisz swoje zapytanie do systemu za pomocą pola zlokalizowanego na dole czatu.
                          Zatwierdz swój wysłanie za pomocą przycisku po prawej stronie lub przyciskiem enter.
                      </a>
                  </li>
                  <li>
                      <a href="https://react.dev/" target="_blank" rel="noopener noreferrer">
                          2. Załącz plik PDF do analizy przez system i opisz twoje wymagania. Można załączyć tylko jeden plik.
                      </a>
                  </li>
                  <li>
                      <a href="https://vite.dev/" target="_blank" rel="noopener noreferrer">
                          3. Jeśli pojawiają się problemy z systemem stosuj się do komunikatów w czacie lub odśwież stronę.
                      </a>
                  </li>
              </ul>

          </section>

      <ChatWindow />

      <div className="ticks"></div>

      <section id="next-steps">
        <div id="docs">
          <svg className="icon" role="presentation" aria-hidden="true">
            <use href="/icons.svg#documentation-icon"></use>
          </svg>
          <h2>Instruckja obsługi</h2>
          <p>Skrócona wersja</p>
          {/*<ul>*/}
          {/*  <li>*/}
          {/*    <a href="https://vite.dev/" target="_blank" rel="noopener noreferrer">*/}
          {/*      1. Wpisz swoje zapytanie do systemu za pomocą pola zlokalizowanego na dole czatu. */}
          {/*      Zatwierdz swój wysłanie za pomocą przycisku po prawej stronie lub przyciskiem enter.*/}
          {/*    </a>*/}
          {/*  </li>*/}
          {/*  <li>*/}
          {/*    <a href="https://react.dev/" target="_blank" rel="noopener noreferrer">*/}
          {/*      2. Załącz plik PDF do analizy przez system i opisz twoje wymagania. Można załączyć tylko jeden plik.*/}
          {/*    </a>*/}
          {/*  </li>*/}
          {/*  <li>*/}
          {/*    <a href="https://vite.dev/" target="_blank" rel="noopener noreferrer">*/}
          {/*      3. Jeśli pojawiają się problemy z systemem stosuj się do komunikatów w czacie lub odśwież stronę.*/}
          {/*    </a>*/}
          {/*  </li>*/}
          {/*</ul>*/}
        </div>
        <div id="social">
          <svg className="icon" role="presentation" aria-hidden="true">
            <use href="/icons.svg#social-icon"></use>
          </svg>
          <h2>Autorzy:</h2>
          <p>Skontaktuj się z nami</p>

          <ul>
            <li>
              <a href="podaj email" target="_blank" rel="noreferrer">
                <svg
                  className="button-icon"
                  role="presentation"
                  aria-hidden="true"
                >
                  <use href="/icons.svg#social-icon"></use>
                </svg>
                Michał Tarnawa
              </a>
            </li>
            <li>
              <a href="Podaj email" target="_blank" rel="noreferrer">
                <svg
                  className="button-icon"
                  role="presentation"
                  aria-hidden="true"
                >
                  <use href="/icons.svg#social-icon"></use>
                </svg>
                Wojciech Grzywocz
              </a>
            </li>
            <li>
              <a href="https://github.com/Grzywocz-W/Company-AI-Assistant" target="_blank">
                <svg
                  className="button-icon"
                  role="presentation"
                  aria-hidden="true"
                >
                  <use href="/icons.svg#github-icon"></use>
                </svg>
                GitHub
              </a>
            </li>
            {/*<li>*/}
            {/*  <a href="https://bsky.app/profile/vite.dev" target="_blank">*/}
            {/*    <svg*/}
            {/*      className="button-icon"*/}
            {/*      role="presentation"*/}
            {/*      aria-hidden="true"*/}
            {/*    >*/}
            {/*      <use href="/icons.svg#bluesky-icon"></use>*/}
            {/*    </svg>*/}
            {/*    Bluesky*/}
            {/*  </a>*/}
            {/*</li>*/}
          </ul>
        </div>
      </section>

      <div className="ticks"></div>
      <section id="spacer"></section>
    </>
  )
}

export default App
