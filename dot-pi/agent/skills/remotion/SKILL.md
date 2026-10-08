---
name: remotion
description: Créer des vidéos soignées avec Remotion (framework React) et un moteur de montage design-ready. Utilise quand une tâche demande de produire une vidéo mp4 (réels, shorts, vidéos promotionnelles) à partir d'un script, de textes ou d'images. Projet préinstallé dans ~/remotion-projects/video-creator.
---

# remotion-video-creator

Guide pour créer des vidéos de qualité "motion design" avec Remotion dans le projet préinstallé.

## Installation (déjà faite — ne pas refaire)

- Projet : `~/remotion-projects/video-creator` (dépendances installées, Chrome headless OK)
- Paquets : remotion 4.x, @remotion/cli, @remotion/transitions, @remotion/google-fonts (Inter + SpaceGrotesk)

## Structure du projet

```
~/remotion-projects/video-creator/
├── package.json          # scripts : render, studio, typecheck
├── remotion.config.ts    # config globale
└── src/
    ├── index.ts          # point d'entrée (registerRoot)
    ├── Root.tsx          # enregistre les 3 compositions + durée totale
    ├── Video.tsx         # ⭐ MOTEUR DE MONTAGE (design system — ne pas casser)
    └── scenes.ts         # ⭐ CONTENU + TYPES — éditer ICI
```

## Le moteur de montage (src/Video.tsx)

C'est un studio de motion design en code. NE PAS modifier sa structure, mais les valeurs sont adaptables :
- **Typographie** : Inter (corps) + SpaceGrotesk (titres), chargées via Google Fonts
- **Hiérarchie visuelle** : kicker (petit label) → titre → sous-titre, barre d'accent
- **Décor** : dégradé radial + vignette, fond jamais plat
- **Transitions de scène** : fade / slide / wipe (26 frames, spring) via @remotion/transitions
- **Animations internes** : révélation mot à mot, apparition en cascade (listes), Ken Burns (images)

## Types de scènes (src/scenes.ts)

| Type | Champs | Usage |
|------|--------|-------|
| `title` | kicker?, text, subtitle? | Ouverture : label + grand titre |
| `text` | text, subtext? | Message central |
| `quote` | quote, author? | Citation avec guillemet décoratif |
| `list` | title?, items[] | Points clés en cascade (max 4-5) |
| `image` | imageUrl, caption?, kenBurns? | Visuel avec zoom lent |
| `end` | text, subtitle? | Carte de fin avec CTA |

**Palettes** (fond/texte/accent) : `midnight` (bleu nuit/orange), `violet` (violet/cyan), `mono` (noir/blanc), `warm` (crème/terracotta).
**Animations** (transitions entre scènes) : `fade`, `slide`, `scale`.

Exemples :
```ts
{ type: "title", durationInFrames: 120, kicker: "VECTOR DYNAMICS", text: "Le design\nen mouvement", palette: "midnight", animation: "scale" }
{ type: "list", durationInFrames: 150, title: "Titre", items: ["Point 1", "Point 2"], palette: "midnight" }
{ type: "image", durationInFrames: 105, imageUrl: "/tmp/photo.png", caption: "Légende", kenBurns: true }
```

## Principes de design à respecter (qualité du montage)

- **Une idée par scène** — jamais deux messages dans la même scène
- **Texte court** : max ~12 mots par scène de texte ; le moteur agrandit la typo
- **Respiration** : laisser 60-120 frames (2-4 s) par scène ; ne pas coller les messages
- **Hiérarchie** : kicker → titre → sous-titre ; un seul accent coloré par scène
- **Cohérence** : choisir 1-2 palettes max par vidéo, garder la même police
- **Image** : toujours télécharger en local d'abord (curl -sL -o /tmp/img.png URL) ; préférer des images nettes (pas de compression)
- **Rythme** : alterner les types de scènes (titre → quote → list → text → image → end)
- **Craftsmanship** : relire les textes (orthographe), vérifier chaque scène via `npx remotion still` avant le rendu final

## Workflow

1. Éditer `src/scenes.ts` (contenu + palette + animation par scène)
2. `cd ~/remotion-projects/video-creator && npx remotion compositions src/index.ts` (vérifier durées)
3. Prévisualiser des images clés : `npx remotion still src/index.ts VideoVertical out/check.png --frame=60`
4. Rendre : `npx remotion render src/index.ts VideoVertical out/video.mp4`
   - **4K par défaut** : `Video16x9` (3840×2160), `VideoVertical` (2160×3840), `VideoSquare` (2160×2160) — tailles définies dans `src/Root.tsx`
   - **Rendu en `--gl=angle`** (déjà réglé dans `remotion.config.ts`) : indispensable, le même rendu 4K en WebGL logiciel (`swangle`) est ~13× plus lent (8 s/frame contre 0,4 s). En cas d'échec, relancer en explicite `--gl=angle` ; `--gl=swangle` seulement en dernier recours.
   - **Toujours ajouter `--timeout=120000 --concurrency=2`** : sur cette machine (8 Go de RAM), le 4K dépasse parfois les 30 s par frame sur les transitions canvas et le rendu avorte (`Timeout (30000ms) exceeded rendering the component at frame 871`). Avec ces flags, 35 s de vidéo se rendent en ~5 min.
   - Durée de référence : 30-45 s de vidéo ≈ 5-12 min en 4K sur cette machine
   - Test rapide : `--frames=0-59` ou `--scale=0.5`
5. Vérifier : `ffprobe -v error -show_entries format=duration,size -show_entries stream=width,height,codec_name -of default=noprint_wrappers=1 out/video.mp4`

## Attention

- La durée totale est calculée dans Root.tsx : somme des scènes + transitions (32 frames × nb de transitions). Si vous ajoutez des scènes, tout est recalculé automatiquement.
- Ne pas modifier les imports fonts ni le `transitionFor` sans tester un rendu.
- Si le rendu échoue : lire l'erreur, corriger, retenter (max 3), puis commenter l'erreur exacte.

## Assets (logo, musique, images)

Le projet a un dossier centralisé :

```
assets/
├── logo/     → logo.svg ou logo.png (remplace le "V" généré partout)
├── images/   → photos/illustrations pour les scènes image
├── audio/    → music.mp3 (musique de fond auto-intégrée avec fondus)
├── videos/   → clips à intégrer
└── lottie/   → animations JSON (motion graphics avancés)
```

### Règles pour l'agent

1. **Toujours télécharger les assets en local AVANT le rendu** :
   - Depuis une URL : `curl -sL -o assets/images/nom.png "URL"`
   - Depuis Google Drive (lien dans l'issue) : extraire le FILE_ID puis
     `composio execute GOOGLEDRIVE_DOWNLOAD_FILE -d '{"fileId":"FILE_ID"}'`
     puis télécharger l'URL signée vers assets/.
2. **Logo de marque** : s'il est fourni (assets/logo/logo.svg), renseigner son
   chemin dans src/brand.ts (BRAND.logoPath) — le moteur l'utilise partout
   (titre, carte de fin, filigrane). Sinon laisser null (logo "V" généré).
3. **Musique** : déposer assets/audio/music.mp3 et renseigner BRAND.audioPath
   dans src/brand.ts. Le moteur gère les fondus d'entrée/sortie tout seul.
4. **Images de scène** : référencer le chemin local dans scenes.ts
   (`imageUrl: "assets/images/photo.png"` ou chemin absolu).
5. **Vérifier que le fichier existe** avant de référencer : `ls -la assets/images/`
6. **Lottie** (motion graphics avancés) : déposer le JSON dans assets/lottie/
   et suivre le skill remotion-video-toolkit (règle lottie.md).

## Voix-off (voix "Thierno" via Cartesia)

Le projet a un pipeline TTS intégré avec la voix clonée "Thierno".

### Workflow pour une nouvelle voix-off

1. Écrire une ligne de narration par scène dans `src/narration.json`
   (une entrée par scène, même ordre que scenes.ts ; `null` = scène muette).
   ⚠️ JSON valide : pas de commentaires, guillemets doubles.
2. Générer les mp3 : `node scripts/generate-voiceover.mjs`
   → crée assets/audio/scene-XX.mp3 et affiche les durées recommandées.
3. Copier les mp3 dans le dossier public : `cp assets/audio/scene-0*.mp3 public/audio/`
4. Dans scenes.ts : ajouter `voiceoverPath: staticFile("audio/scene-XX.mp3")`
   à chaque scène concernée, et ajuster durationInFrames au minimum
   recommandé par le script (durée audio + marge).
5. Rendre la vidéo — la voix démarre au début de chaque scène.

### Règles

- La clé API est dans le fichier `.env` (ne jamais l'exposer ni la committer).
- Le modèle utilisé : sonic-2 (multilingue, dont français).
- Narration : phrases courtes et naturelles (2-12 s par scène), une idée par scène.
- Réécrire la narration = relancer generate-voiceover.mjs puis re-rendre.
- Vérifier qu'une piste audio est bien présente : ffprobe (codec_type=audio).
