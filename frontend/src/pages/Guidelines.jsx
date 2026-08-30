import LegalPageShell from '../components/LegalPageShell'

const PROCESSORS = [
  {
    n: 'A.',
    service: 'Mistral AI',
    role: "Transcription de l'audio en texte",
    data: "L'enregistrement audio de la réunion",
    dpaUrl: 'https://legal.mistral.ai/terms/data-processing-addendum',
    dpaLabel: 'Voir le DPA →',
  },
  {
    n: 'B.',
    service: 'Together AI',
    role: 'Génération du compte-rendu',
    data: 'La transcription textuelle de la réunion',
    dpaUrl: 'https://trust.together.ai/',
    dpaLabel: 'Trust Center →',
  },
  {
    n: 'C.',
    service: 'Resend',
    role: "Envoi des e-mails (codes de vérification, réinitialisation)",
    data: 'Votre adresse e-mail',
    dpaUrl: 'https://resend.com/legal/dpa',
    dpaLabel: 'Voir le DPA →',
  },
  {
    n: 'D.',
    service: 'Railway',
    role: 'Hébergement de la base de données (comptes et comptes-rendus)',
    data: "L'ensemble des données de votre compte",
    dpaUrl: 'https://railway.com/legal/dpa',
    dpaLabel: 'Voir le DPA →',
  },
  {
    n: 'E.',
    service: 'Google',
    role: "Lecture et écriture de votre agenda — uniquement si vous activez l'intégration Google Calendar",
    data: 'Titre, horaire et compte-rendu de vos réunions, événements de votre agenda',
    dpaUrl: 'https://cloud.google.com/terms/data-processing-addendum/',
    dpaLabel: 'Voir le DPA →',
  },
]

export default function Guidelines() {
  return (
    <LegalPageShell title="Conditions d'utilisation" lastUpdated="23 août 2026">
      <h2 className="font-display text-lg uppercase tracking-[-1px] mb-3">Ce que nous faisons de vos réunions</h2>
      <div className="border-4 border-ink p-6 font-mono text-sm leading-[1.7] mb-8">
        <p className="m-0">
          What&apos;s On Meeting enregistre vos réunions, les transcrit puis en génère un compte-rendu
          (résumé, décisions, actions). Vous décidez quelles réunions sont enregistrées et gardez le
          contrôle de vos données à tout moment.
        </p>
      </div>

      <h2 className="font-display text-lg uppercase tracking-[-1px] mb-3">Sous-traitants</h2>
      <div className="border-4 border-ink mb-2 font-mono text-sm leading-[1.6]">
        <p className="m-0 p-6 pb-3.5">
          Pour fonctionner, What&apos;s On Meeting fait appel aux prestataires suivants. Chacun ne reçoit
          que les données nécessaires à sa tâche :
        </p>
        {PROCESSORS.map(p => (
          <div key={p.n} className="flex gap-3 py-3.5 px-6 border-t-[3px] border-ink flex-wrap">
            <span className="font-display shrink-0">{p.n}</span>
            <span className="flex-1 min-w-0">
              <b>{p.service}</b> — {p.role}.<br />
              <span className="text-muted">Reçoit : {p.data}.</span>
            </span>
            {p.dpaUrl && (
              <a
                href={p.dpaUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="shrink-0 self-start font-mono text-xs uppercase tracking-[1px] underline font-bold whitespace-nowrap"
              >
                {p.dpaLabel}
              </a>
            )}
          </div>
        ))}
      </div>
      <p className="font-mono text-xs text-muted mb-8 px-1">
        Certains de ces prestataires peuvent traiter vos données hors de l&apos;Union européenne.
        Le DPA de Together AI n&apos;est pas publié publiquement — un exemplaire est disponible sur
        demande directement auprès de Together AI. Pour toute question sur un prestataire précis,
        contactez-nous.
      </p>

      <h2 className="font-display text-lg uppercase tracking-[-1px] mb-3">Votre responsabilité en tant qu&apos;organisateur</h2>
      <div className="border-4 border-ink p-6 font-mono text-sm leading-[1.7] mb-8">
        <p className="m-0 mb-3.5">
          Quand vous renseignez l&apos;adresse e-mail d&apos;un participant pour lui associer un
          compte-rendu, et que cette personne n&apos;a pas de compte What&apos;s On Meeting, <b>vous
          êtes responsable</b> de l&apos;informer et d&apos;obtenir son accord pour la collecte de
          cette donnée (son adresse e-mail).
        </p>
        <p className="m-0">
          What&apos;s On Meeting agit uniquement sur vos instructions pour enregistrer et traiter la
          réunion ; nous ne sommes pas partie à la relation entre vous et vos invités. En conséquence,
          aucune réclamation ni demande de dédommagement liée à la participation d&apos;une personne
          sans compte ne peut être adressée à What&apos;s On Meeting — elle relève de votre seule
          responsabilité en tant qu&apos;organisateur.
        </p>
      </div>

      <h2 className="font-display text-lg uppercase tracking-[-1px] mb-3">Vos droits</h2>
      <div className="border-4 border-ink p-6 font-mono text-sm leading-[1.7]">
        <p className="m-0 mb-2">
          Conformément au RGPD, vous pouvez demander l&apos;accès, la rectification ou la suppression de
          vos données à tout moment.
        </p>
        <p className="m-0">
          Si votre demande n&apos;aboutit pas, vous pouvez saisir l&apos;autorité de protection des
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
    </LegalPageShell>
  )
}
