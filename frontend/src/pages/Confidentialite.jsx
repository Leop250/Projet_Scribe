import { useNavigate } from 'react-router'
import Logo from '../components/Logo'

const POINTS = [
  { n: 'A.', t: 'Nom, tracé de signature et horodatage — rien d’autre.' },
  { n: 'B.', t: 'Utilisées uniquement comme preuve de présence à la réunion enregistrée.' },
  { n: 'C.', t: 'Conservées par l’organisateur, supprimables sur simple demande.' },
  { n: 'D.', t: 'Jamais partagées ni revendues à des tiers.' },
]

export default function Confidentialite() {
  const navigate = useNavigate()

  return (
    <div className="min-h-[100dvh] bg-paper text-ink font-body flex flex-col">
      <div className="px-5 py-5">
        <Logo size={22} />
      </div>

      <div id="main-content" tabIndex={-1} className="flex-1 px-5 pb-14 max-w-[560px] w-full mx-auto animate-slam">
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="cursor-pointer bg-transparent border-none p-0 font-mono text-xs uppercase tracking-[2px] mb-3.5 inline-block"
        >
          ← Retour
        </button>

        <h1 className="font-display text-[34px] uppercase tracking-[-2px] m-0 mb-5 leading-none">
          Confidentialité
        </h1>

        <div className="border-4 border-ink p-6 font-mono text-sm leading-[1.7]">
          <p className="m-0 mb-3.5">
            En signant la feuille de présence, tu transmets des données personnelles
            à l’organisateur de la réunion. Voici ce qui est collecté et pourquoi :
          </p>
          {POINTS.map(p => (
            <div key={p.n} className="flex gap-3 py-2.5 border-t-[3px] border-ink">
              <span className="font-display shrink-0">{p.n}</span>
              <span>{p.t}</span>
            </div>
          ))}
        </div>

        <div className="border-4 border-ink border-t-0 p-6 font-mono text-sm leading-[1.7]">
          <p className="m-0 mb-2">
            Conformément au RGPD, tu peux demander l’accès, la rectification ou la
            suppression de ces données en contactant l’organisateur de la réunion.
          </p>
          <p className="m-0">
            Si ta demande n’aboutit pas, tu peux saisir l’autorité de protection des
            données compétente — en France, la{' '}
            <a
              href="https://www.cnil.fr/fr/plaintes"
              target="_blank"
              rel="noopener noreferrer"
              className="underline font-bold"
            >
              CNIL
            </a>.
          </p>
        </div>
      </div>
    </div>
  )
}
