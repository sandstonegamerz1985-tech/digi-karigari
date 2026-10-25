import { useEffect, useRef } from "react";
import { useLang } from "../i18n";

// A popup shown on the visitor's first visit: "Choose your language / अपनी भाषा चुनें".
// Once a language is picked it is remembered in the browser and the popup never appears again.
// (The language button in the navbar can still change it later.)
export default function LanguagePrompt() {
  const { needsChoice, setLang } = useLang();
  const firstButton = useRef(null);

  useEffect(() => {
    if (needsChoice && firstButton.current) firstButton.current.focus();
  }, [needsChoice]);

  if (!needsChoice) return null;

  return (
    <div className="modal-backdrop">
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby="lang-title">
        <h2 id="lang-title">
          Choose your language
          <br />
          अपनी भाषा चुनें
        </h2>
        <p className="muted small">You can change this any time from the menu. / आप इसे कभी भी मेनू से बदल सकते हैं।</p>
        <div className="row wrap modal-actions">
          <button ref={firstButton} className="btn" onClick={() => setLang("en")}>
            English
          </button>
          <button className="btn" onClick={() => setLang("hi")}>
            हिन्दी
          </button>
        </div>
      </div>
    </div>
  );
}
