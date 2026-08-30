import LegalPageShell from '../components/LegalPageShell'

export default function MentionsLegales() {
  return (
    <LegalPageShell title="Mentions légales" lastUpdated="29 août 2026">
      <h2 className="font-display text-lg uppercase tracking-[-1px] mb-3">Éditeur</h2>
      <div className="border-4 border-ink p-6 font-mono text-sm leading-[1.7] mb-8">
        <p className="m-0 mb-3.5">
          What&apos;s On Meeting est un projet étudiant, édité et développé par : Younes, Kylian,
          Léopold et Matteo.
        </p>
        <p className="m-0">
          Contact :{' '}
          <a href="mailto:contact@scribeapp.com" className="underline font-bold">
            contact@scribeapp.com
          </a>
        </p>
      </div>

      <h2 className="font-display text-lg uppercase tracking-[-1px] mb-3">Directeur de la publication</h2>
      <div className="border-4 border-ink p-6 font-mono text-sm leading-[1.7] mb-8">
        <p className="m-0">
          La direction de la publication est assurée conjointement par Younes, Kylian, Léopold et
          Matteo, en leur qualité d&apos;éditeurs du projet.
        </p>
      </div>

      <h2 className="font-display text-lg uppercase tracking-[-1px] mb-3">Hébergement</h2>
      <div className="border-4 border-ink p-6 font-mono text-sm leading-[1.7] mb-8">
        <p className="m-0">
          L&apos;application et sa base de données sont hébergées par :<br />
          <b>Railway Corporation</b><br />
          548 Market St PMB 68956, San Francisco, CA 94104, États-Unis<br />
          <a href="https://railway.com" target="_blank" rel="noopener noreferrer" className="underline font-bold">
            railway.com
          </a>
        </p>
      </div>

      <h2 className="font-display text-lg uppercase tracking-[-1px] mb-3">Propriété intellectuelle</h2>
      <div className="border-4 border-ink p-6 font-mono text-sm leading-[1.7] mb-8">
        <p className="m-0">
          L&apos;ensemble des éléments composant What&apos;s On Meeting (textes, interface, logo,
          code source) est protégé par le droit d&apos;auteur. Toute reproduction ou représentation,
          totale ou partielle, sans autorisation est interdite.
        </p>
      </div>

      <h2 className="font-display text-lg uppercase tracking-[-1px] mb-3">Données personnelles</h2>
      <div className="border-4 border-ink p-6 font-mono text-sm leading-[1.7]">
        <p className="m-0 mb-3.5">
          Le traitement de vos données personnelles, la liste de nos sous-traitants et vos droits
          RGPD sont détaillés dans nos{' '}
          <a href="/guidelines" target="_blank" rel="noopener noreferrer" className="underline font-bold">
            conditions d&apos;utilisation
          </a>.
        </p>
        <p className="m-0">
          Vous pouvez également saisir la{' '}
          <a
            href="https://www.cnil.fr/fr/plaintes"
            target="_blank"
            rel="noopener noreferrer"
            className="underline font-bold"
          >
            CNIL
          </a>{' '}
          en cas de litige non résolu.
        </p>
      </div>
    </LegalPageShell>
  )
}
