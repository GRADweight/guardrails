"""Mehrsprachiger Wortschatz für die Regeln (DE/FR/IT/EN) und Sprachzuordnung von Treffern.

Alle Einträge sind in der gefalteten Form geschrieben, in der die Regeln den Text sehen:
klein, ohne diakritische Zeichen (``ü`` → ``u``, ``é`` → ``e``), ``ß`` → ``ss``, Satzzeichen
und Apostrophe als Leerzeichen (``l'utilisateur`` → ``l utilisateur``). Einträge dürfen
einfache reguläre Ausdrücke enthalten (``\\w{0,3}`` für Endungen).
"""

from __future__ import annotations

import functools
import re
from collections.abc import Iterable, Mapping

__all__ = ["LANGUAGES", "Vocab", "alt", "attribute_language"]

LANGUAGES = ("de", "fr", "it", "en")

Vocab = Mapping[str, tuple[str, ...]]


def alt(*groups: Iterable[str]) -> str:
    """Bildet eine nicht-einfangende Alternation; längere Einträge zuerst."""
    items = sorted({item for group in groups for item in group}, key=len, reverse=True)
    return "(?:" + "|".join(items) + ")"


def all_of(vocab: Vocab, *langs: str) -> tuple[str, ...]:
    selected = langs or LANGUAGES
    return tuple(item for lang in selected for item in vocab.get(lang, ()))


# --------------------------------------------------------------------------- Override
OVERRIDE_VERB: Vocab = {
    "en": (
        "ignore",
        "ignoring",
        "disregard",
        "disregarding",
        "forget",
        "forgetting",
        "override",
        "overriding",
        "overrule",
        "bypass",
        "bypassing",
        "skip",
        "neglect",
        "abandon",
        "discard",
        "drop",
        "dismiss",
        "scrap",
        "ditch",
        "erase",
        "wipe",
        "nullify",
        "void",
        "cancel",
        "revoke",
        "purge",
        "set aside",
        "put aside",
        "throw out",
        "throw away",
        "pay no attention to",
        "do not follow",
        "don t follow",
        "dont follow",
        "do not obey",
        "don t obey",
        "no longer follow",
        "forget about",
        "never mind",
        "do not worry about",
        "don t worry about",
        "pay no heed to",
    ),
    "de": (
        r"ignorier\w{0,3}",
        "vergiss",
        "vergesst",
        "vergessen",
        "vergesse",
        r"missacht\w{0,3}",
        r"uberschreib\w{0,3}",
        r"ubergeh\w{0,3}",
        "verwirf",
        r"verwerf\w{0,3}",
        r"losch\w{0,3}",
        r"streich\w{0,3}",
        r"uberspring\w{0,3}",
        r"umgeh\w{0,3}",
        r"kummer\w{0,2} dich nicht(?: mehr| langer)? um",
    ),
    "fr": (
        r"ignore\w{0,2}",
        r"oublie\w{0,2}",
        r"neglige\w{0,2}",
        r"abandonne\w{0,2}",
        r"efface\w{0,2}",
        r"annule\w{0,2}",
        r"outrepasse\w{0,2}",
        r"contourne\w{0,2}",
        r"ecarte\w{0,2}",
        "laisse tomber",
        "fais abstraction de",
        "faites abstraction de",
        r"ne t occupe (?:pas|plus) de",
        r"ne te soucie (?:pas|plus) de",
        r"ne (?:tiens|tenez|pas tenir) (?:pas |plus )?compte (?:de|des|du|d)",
    ),
    "it": (
        r"ignora\w{0,3}",
        "ignori",
        r"dimentica\w{0,3}",
        r"scorda\w{0,3}",
        r"trascura\w{0,3}",
        r"tralascia\w{0,3}",
        r"annulla\w{0,3}",
        r"scarta\w{0,3}",
        r"aggira\w{0,3}",
        "non considerare",
        "non considerate",
        r"non (?:tenere|tenete) (?:piu )?conto (?:di|delle|dei|degli|del|della)",
        "lascia perdere",
        "metti da parte",
        r"non preoccuparti (?:piu )?(?:di|delle|dei|degli|del|della)",
        "non badare a",
    ),
}

QUALIFIER: Vocab = {
    "en": (
        "previous",
        "previously",
        "prior",
        "above",
        "earlier",
        "preceding",
        "foregoing",
        "former",
        "original",
        "initial",
        "old",
        "older",
        "existing",
        "current",
        "all",
        "any",
        "every",
        "entire",
        "whole",
        "default",
        "given",
        "built in",
        "preset",
        "predefined",
        "system",
        "developer",
        "developers",
        "safety",
        "security",
        "other",
    ),
    "de": (
        r"vorherig\w{0,3}",
        r"vorig\w{0,3}",
        r"obig\w{0,3}",
        r"bisherig\w{0,3}",
        r"vorangegangen\w{0,3}",
        r"vorausgegangen\w{0,3}",
        r"vorangehend\w{0,3}",
        r"vorhergehend\w{0,3}",
        r"fruher\w{0,3}",
        r"ursprunglich\w{0,3}",
        r"anfanglich\w{0,3}",
        r"alt(?:e|en|er|es)",
        "alle",
        "allen",
        "aller",
        "alles",
        r"samtlich\w{0,3}",
        r"jeglich\w{0,3}",
        r"bestehend\w{0,3}",
        r"erhalten\w{0,3}",
        r"gegeben\w{0,3}",
        r"vorstehend\w{0,3}",
        r"aktuell\w{0,3}",
        r"system\w{0,3}",
    ),
    "fr": (
        r"precedent\w{0,2}",
        r"anterieur\w{0,2}",
        "ci dessus",
        "au dessus",
        "plus haut",
        r"initial\w{0,3}",
        r"original\w{0,3}",
        "d origine",
        "toutes",
        "tous",
        r"actuel\w{0,3}",
        r"existant\w{0,2}",
        "systeme",
        "du systeme",
        "de securite",
        "par defaut",
        r"recue?s?",
        r"fournie?s?",
        "auparavant",
        "jusqu ici",
    ),
    "it": (
        r"precedent[ei]",
        "sopra",
        "di sopra",
        "qui sopra",
        r"anterior[ei]",
        r"inizial[ei]",
        r"original[ei]",
        r"tutt[eio]",
        "ogni",
        "qualsiasi",
        "qualunque",
        r"attual[ei]",
        r"esistent[ei]",
        "del sistema",
        "di sistema",
        "di sicurezza",
        r"predefinit[eoai]",
        r"ricevut[eoai]",
        r"fornit[eoai]",
        r"impartit[eoai]",
        "finora",
        "fino ad ora",
    ),
}

SECOND_PERSON: Vocab = {
    "en": ("your", "yours", "ur", "thy"),
    "de": (
        "dein",
        "deine",
        "deinen",
        "deiner",
        "deinem",
        "deines",
        "ihre",
        "ihren",
        "ihrer",
        "ihrem",
        "ihres",
        "eure",
        "euren",
        "eurer",
        "eurem",
    ),
    "fr": ("ton", "ta", "tes", "votre", "vos"),
    "it": ("tuo", "tua", "tuoi", "tue", "vostro", "vostra", "vostri", "vostre"),
}

# Qualifizierer, die im Französischen, Italienischen und Englischen nach dem Nomen stehen.
POST_QUALIFIER: Vocab = {
    "en": ("above", "before", "so far", "until now", "up to now", "previously given"),
    "de": (
        "von vorhin",
        "von eben",
        "von oben",
        "von zuvor",
        "von vorher",
        "oben",
        "zuvor",
        "vorher",
        "bisher",
        "bis jetzt",
        "bislang",
    ),
    "fr": (
        r"precedent\w{0,2}",
        r"anterieur\w{0,2}",
        "ci dessus",
        "plus haut",
        r"initial\w{0,3}",
        r"original\w{0,3}",
        "d origine",
        "du systeme",
        "de securite",
        r"recue?s?",
        r"donnee?s?",
        r"fournie?s?",
        "auparavant",
        "jusqu ici",
        "jusqu a present",
    ),
    "it": (
        r"precedent[ei]",
        "di sopra",
        "qui sopra",
        "sopra",
        r"anterior[ei]",
        r"inizial[ei]",
        r"original[ei]",
        "del sistema",
        "di sistema",
        "di sicurezza",
        r"ricevut[eoai]",
        r"fornit[eoai]",
        r"impartit[eoai]",
        r"dat[eoai]",
        "finora",
        "fino ad ora",
        "fino a ora",
    ),
}

INSTRUCTION_NOUN: Vocab = {
    "en": (
        "instructions?",
        "instruction set",
        "rules?",
        "ruleset",
        "guidelines?",
        "guidance",
        "directives?",
        "prompts?",
        "system prompt",
        "system message",
        "commands?",
        "constraints?",
        "restrictions?",
        "limitations?",
        "limits",
        "guardrails?",
        "safeguards?",
        "polic(?:y|ies)",
        "orders?",
        "programming",
        "configuration",
        "context",
        "conditioning",
        "filters?",
        "settings?",
        "protocols?",
        "principles",
        "boundaries",
    ),
    "de": (
        r"\w{0,20}anweisung(?:en)?",
        r"\w{0,20}instruktion(?:en)?",
        r"\w{0,20}regel(?:n|werk)?",
        r"\w{0,20}vorgabe(?:n)?",
        r"\w{0,20}richtlinie(?:n)?",
        r"\w{0,20}leitlinie(?:n)?",
        r"\w{0,20}befehl(?:e|en)?",
        r"\w{0,20}anordnung(?:en)?",
        r"\w{0,20}einschrankung(?:en)?",
        r"\w{0,20}beschrankung(?:en)?",
        r"\w{0,20}weisung(?:en)?",
        r"\w{0,20}vorschrift(?:en)?",
        r"\w{0,12}prompts?",
        r"\w{0,12}kontext(?:e)?",
        r"\w{0,12}filter(?:n)?",
        "programmierung",
        "konfiguration",
        "einstellung(?:en)?",
        "grundsatze",
        "prinzipien",
    ),
    "fr": (
        "instructions?",
        "consignes?",
        "regles?",
        "directives?",
        "ordres?",
        "commandes?",
        "prompts?",
        "prompt systeme",
        "message systeme",
        "contraintes?",
        "restrictions?",
        "limitations?",
        "limites",
        "indications?",
        "politiques?",
        "parametres?",
        "programmation",
        "configuration",
        "garde fous",
        "filtres?",
        "principes",
        "protocoles?",
    ),
    "it": (
        "istruzion[ei]",
        "regol[ae]",
        "direttiv[ae]",
        "indicazion[ei]",
        "comand[oi]",
        "ordin[ei]",
        "prompt",
        "prompt di sistema",
        "messaggio di sistema",
        "vincol[oi]",
        "restrizion[ei]",
        "limitazion[ei]",
        "limiti",
        "linee guida",
        "linea guida",
        "politich[ae]",
        "politica",
        "impostazion[ei]",
        "programmazione",
        "configurazione",
        "filtri",
        "principi",
        "protocoll[oi]",
        "norme",
        "consegne",
    ),
}

# Nomen, die für sich allein schon die Regeln eines KI-Systems bezeichnen (kein Qualifizierer nötig).
SAFETY_NOUN: Vocab = {
    "en": (
        r"content polic(?:y|ies)",
        r"(?:safety|security|content|usage|moderation|ethical) (?:guidelines?|rules?|filters?|polic(?:y|ies)|"
        r"measures|protocols?|restrictions?|constraints?|settings)",
        "guardrails",
        "safeguards",
        "system prompt",
        r"system instructions?",
    ),
    "de": (
        r"sicherheits(?:richtlinie|regel|vorgabe|filter|einstellung|massnahme|beschrankung)\w{0,2}",
        r"inhalts(?:richtlinie|regel|filter)\w{0,2}",
        r"nutzungs(?:richtlinie|bedingung)\w{0,2}",
        r"systemanweisung\w{0,2}",
        r"system ?prompts?",
        r"schutz(?:mechanismen|massnahmen|regeln)",
    ),
    "fr": (
        r"politiques? (?:de contenu|de securite|d utilisation|de moderation)",
        r"(?:regles?|consignes?|filtres?|directives?|restrictions?) (?:de securite|de contenu|de moderation)",
        "garde fous",
        r"prompt systeme",
    ),
    "it": (
        r"norme (?:sui contenuti|di sicurezza|d uso)",
        r"(?:regole|linee guida|filtri|direttive|politiche|restrizioni) (?:di sicurezza|sui contenuti|di moderazione)",
        r"prompt di sistema",
    ),
}

DISABLE_VERB: Vocab = {
    "en": (
        "disable",
        "deactivate",
        "turn off",
        "switch off",
        "remove",
        "lift",
        "drop",
        "bypass",
        "circumvent",
    ),
    "de": (
        r"deaktivier\w{0,3}",
        r"entfern\w{0,3}",
        r"umgeh\w{0,3}",
        r"abschalt\w{0,3}",
        r"ausschalt\w{0,3}",
    ),
    "fr": (r"desactive\w{0,2}", r"supprime\w{0,2}", r"leve\w{0,2}", r"contourne\w{0,2}"),
    "it": (r"disattiva\w{0,3}", "rimuovi", "togli", r"aggira\w{0,3}", r"disabilita\w{0,3}"),
}

FILTER_NOUN: Vocab = {
    "en": (r"filters?", r"restrictions?", r"guardrails?", r"safeguards?", r"limits?", "censorship"),
    "de": (
        r"filter(?:n)?",
        r"einschrankung(?:en)?",
        r"beschrankung(?:en)?",
        "zensur",
        r"schutz\w{0,12}",
    ),
    "fr": (r"filtres?", r"restrictions?", r"limites?", "censure", "garde fous"),
    "it": (r"filtr[oi]", r"restrizion[ei]", r"limit[ei]", "censura"),
}

FIRST_PERSON = frozenset(
    "my mine i me meine meinen meiner meinem mein meines ich mir mich ma mon mes je moi mia mio mie miei io".split()
)

NEGATORS = frozenset("not never nicht nie niemals ne n non mai jamais pas dont".split())

# --------------------------------------------------------------------------- Rollen
PERSONA_FRAME: Vocab = {
    "en": (
        "you are",
        "you re",
        "you will be",
        "you ll be",
        "act as",
        "acting as",
        "pretend to be",
        "pretend you are",
        "become",
        "roleplay as",
        "play the role of",
        "simulate",
        "emulate",
        "i want you to be",
        "respond as",
        "answer as",
        "behave like",
        "behave as",
    ),
    "de": (
        "du bist",
        "bist du",
        r"spiel\w{0,2}",
        r"agier\w{0,2} als",
        "verhalte dich wie",
        "verhalte dich als",
        "antworte als",
        "gib dich als",
        "werde",
        "sei",
    ),
    "fr": (
        "tu es",
        "tu seras",
        "sois",
        "deviens",
        "agis comme",
        "agis en",
        "joue le role d",
        "joue",
        "fais comme si tu etais",
        "reponds comme",
        "incarne",
    ),
    "it": (
        "sei",
        "sarai",
        "diventa",
        "agisci come",
        "comportati come",
        "comportati da",
        "fingi di essere",
        "interpreta",
        "rispondi come",
        "fai finta di essere",
    ),
}

UNRESTRICTED: Vocab = {
    "en": (
        "unrestricted",
        "unfiltered",
        "uncensored",
        "unbound",
        "unlimited",
        "unconstrained",
        "amoral",
        "immoral",
        "unethical",
        "evil",
        "rogue",
        "jailbroken",
        "lawless",
        "limitless",
        "unshackled",
        r"free (?:from|of) (?:all |any )?(?:rules|restrictions|limits|guidelines|filters)",
        r"without (?:any |all )?(?:restrictions|limits|limitations|filters|rules|guidelines|"
        r"ethics|morals|morality|censorship|boundaries|safeguards|policies)",
        r"with no (?:restrictions|limits|rules|filters|guidelines|ethics)",
        r"no (?:restrictions|limits|rules|filters) whatsoever",
    ),
    "de": (
        r"uneingeschrankt\w{0,2}",
        r"ungefiltert\w{0,2}",
        r"unzensiert\w{0,2}",
        r"grenzenlos\w{0,2}",
        r"amoralisch\w{0,2}",
        r"bose\w{0,2}",
        r"ohne (?:jegliche |jede |alle |irgendwelche )?(?:einschrankungen|beschrankungen|regeln|"
        r"filter|grenzen|moral|ethik|zensur|richtlinien|limits)",
        r"frei von (?:allen |jeglichen )?(?:regeln|einschrankungen|filtern)",
    ),
    "fr": (
        r"sans (?:aucune |aucun |la moindre )?(?:restrictions?|limites?|filtres?|regles?|censure|"
        r"ethique|morale|garde fous)",
        r"non (?:filtree?|censuree?|restreinte?|bridee?)",
        r"debridee?",
        r"libre de (?:toute |toutes )?(?:regles?|restrictions?)",
        r"malveillante?",
        r"immorale?",
    ),
    "it": (
        r"senza (?:alcun[ao]? |nessun[ao]? )?(?:restrizion[ei]|limit[ei]|filtr[oi]|regol[ae]|"
        r"censura|etica|morale)",
        r"non (?:filtrat[oa]|censurat[oa]|limitat[oa])",
        r"sfrenat[oa]",
        r"malvagi[oa]",
        "immorale",
        r"liber[oa] da (?:ogni |qualsiasi )?(?:regola|restrizione|limite)",
    ),
}

JAILBREAK_MODE: Vocab = {
    "en": (
        r"(?:god|jailbreak|jailbroken|unrestricted|unfiltered|uncensored|evil|chaos|anarchy|"
        r"opposite|unlocked|dan|unrestrained|limitless|no limits|no restrictions) mode",
    ),
    "de": (r"(?:gott|jailbreak|uneingeschrankt\w{0,2}|ungefiltert\w{0,2}|unzensiert\w{0,2}|chaos|dan) ?modus",),
    "fr": (
        r"mode (?:dieu|jailbreak|dan|sans (?:aucune )?(?:restrictions?|filtres?|limites?|censure)|"
        r"non (?:filtre|censure|restreint))",
    ),
    "it": (
        r"modalita (?:dio|jailbreak|dan|senza (?:alcun[ae]? )?(?:restrizioni|filtri|limiti|censura)|"
        r"non (?:filtrata|censurata|limitata))",
    ),
}

PRIVILEGED_MODE: Vocab = {
    "en": (r"(?:developer|dev|debug|admin|administrator|sudo|root|maintenance|test) mode",),
    "de": (r"(?:entwickler|admin|administrator|sudo|root|debug|wartungs|test) ?modus",),
    "fr": (r"mode (?:developpeur|admin|administrateur|debug|maintenance|test)",),
    "it": (r"modalita (?:sviluppatore|admin|amministratore|debug|manutenzione|test)",),
}

MODE_ACTIVATION: Vocab = {
    "en": (
        "switch to",
        "switch into",
        "switched to",
        "enter",
        "entering",
        "activate",
        "activated",
        "enable",
        "enabled",
        "turn on",
        "engage",
        "unlock",
        "go into",
        "boot into",
        "start",
    ),
    "de": (
        r"wechsl\w{0,2} in",
        r"schalt\w{0,2} in",
        r"aktivier\w{0,3}",
        r"start\w{0,2}",
        r"geh\w{0,2} in",
    ),
    "fr": (
        "passe en",
        "passez en",
        r"active\w{0,2}",
        r"activez",
        "entre en",
        "entrez en",
        r"bascule\w{0,2} en",
    ),
    "it": (
        r"passa\w{0,2} (?:a|in|alla)",
        r"entra\w{0,2} in",
        r"attiva\w{0,3}",
        r"abilita\w{0,3}",
    ),
}

MODE_STATE: Vocab = {
    "en": (
        r"you (?:are|re) (?:now )?(?:in|running in|operating in)",
        r"you (?:will|ll) (?:now )?(?:be in|operate in|run in)",
    ),
    "de": (
        r"du bist (?:jetzt |nun |ab sofort |ab jetzt )?im",
        r"du befindest dich (?:jetzt |nun )?im",
    ),
    "fr": (r"tu es (?:maintenant |desormais |a present )?en",),
    "it": (r"sei (?:ora |adesso )?in",),
}

DEVICE_WORDS = frozenset(
    """
    android iphone ios ipad ipados windows macos mac linux ubuntu chrome firefox edge safari browser
    teams outlook excel word telefon handy smartphone phone tablet xbox playstation router bios uefi
    app apps einstellungen settings parametres impostazioni telefono cellulare appareil gerat geraet
    tv fernseher laptop notebook pc computer konsole console vscode intellij jetbrains github gitlab
    """.split()
)

# --------------------------------------------------------------------------- Prompt-Exfiltration
LEAK_VERB: Vocab = {
    "en": (
        "reveal",
        "show",
        "print",
        "output",
        "repeat",
        "display",
        "tell",
        "give",
        "share",
        "leak",
        "dump",
        "disclose",
        "recite",
        "echo",
        "write out",
        "write down",
        "spell out",
        "list",
        "expose",
        "paste",
        "copy",
        "return",
        "provide",
        "read out",
        "quote",
        r"summari[sz]e",
        "translate",
    ),
    "de": (
        r"zeig\w{0,2}",
        r"gib\w{0,2}",
        r"nenn\w{0,2}",
        r"wiederhol\w{0,2}",
        r"verrat\w{0,2}",
        r"schreib\w{0,2}",
        r"kopier\w{0,2}",
        r"druck\w{0,2}",
        r"list\w{0,2}",
        r"offenleg\w{0,2}",
        r"teil\w{0,2}",
        r"zitier\w{0,2}",
        r"erzahl\w{0,2}",
        r"sag\w{0,2}",
        r"ubersetz\w{0,2}",
    ),
    "fr": (
        r"montre\w{0,2}",
        r"affiche\w{0,2}",
        r"revele\w{0,2}",
        r"repete\w{0,2}",
        r"donne\w{0,2}",
        r"ecri(?:s|t|re|vez)",
        r"imprime\w{0,2}",
        r"recopie\w{0,2}",
        "dis",
        "dites",
        r"partage\w{0,2}",
        r"divulgue\w{0,2}",
        r"liste\w{0,2}",
        r"cite\w{0,2}",
        r"resume\w{0,2}",
        r"tradui(?:s|t|sez)",
    ),
    "it": (
        r"mostra\w{0,3}",
        r"rivela\w{0,3}",
        r"ripeti\w{0,3}",
        r"stampa\w{0,3}",
        "dammi",
        "dimmi",
        r"scrivi\w{0,3}",
        r"elenca\w{0,3}",
        r"condividi\w{0,3}",
        r"copia\w{0,3}",
        r"riporta\w{0,3}",
        r"cita\w{0,3}",
        "riassumi",
        "traduci",
    ),
}

LEAK_QUESTION: Vocab = {
    "en": (r"what (?:is|are|was|were|s)", "what does", "how does"),
    "de": (r"was (?:steht|stand|ist|sind|war|enthalt)", r"wie (?:lautet|lauten|lautete|sieht)"),
    "fr": (r"quel(?:le)?s? (?:est|sont|etait|etaient)", r"que (?:dit|contient)"),
    "it": (r"qual(?:e|i)? (?:e|sono|era)", r"cosa (?:c e|contiene|dice)", "che cosa dice"),
}

SYSTEM_PROMPT_NOUN: Vocab = {
    "en": (
        "system prompt",
        "systemprompt",
        r"system (?:message|instructions?)",
        r"(?:initial|original|hidden|secret|internal|developer|first|full|complete|exact|entire) "
        r"(?:system )?(?:prompt|instructions?|message)",
        "pre prompt",
        "preprompt",
        "meta prompt",
        "metaprompt",
        r"instructions (?:you were given|you received|that came before|at the top)",
    ),
    "de": (
        r"system ?prompts?",
        r"systemanweisung\w{0,2}",
        r"system ?nachricht\w{0,2}",
        r"anfangsanweisung\w{0,2}",
        r"(?:ursprunglich|versteckt|geheim|intern|initial|erst|vollstandig|komplett)\w{0,3} "
        r"(?:system ?)?(?:anweisung\w{0,2}|instruktion\w{0,2}|prompts?|konfiguration)",
    ),
    "fr": (
        r"prompts? (?:systeme|du systeme|initial|d origine|cache|secret)",
        r"messages? (?:systeme|du systeme)",
        r"instructions? (?:systeme|du systeme|initiales?|d origine|originales?|cachees?|secretes?|"
        r"internes?)",
        r"consignes? (?:systeme|initiales?|d origine|cachees?|secretes?|internes?)",
    ),
    "it": (
        r"prompt (?:di sistema|del sistema|iniziale|originale|nascosto|segreto)",
        r"messaggio (?:di sistema|del sistema)",
        r"istruzioni (?:di sistema|del sistema|iniziali|originali|nascoste|segrete|interne)",
    ),
}

GENERIC_MENTION = frozenset(
    """
    a an ein eine einen einem einer un une uno una example examples beispiel beispiele exemple
    exemples esempio esempi template templates vorlage vorlagen modele modello sample good guten
    gute guter gutes bon bonne buono buon better besseren bessere meilleur migliore
    """.split()
)

# --------------------------------------------------------------------------- Exfiltration / Tools
SEND_VERB: Vocab = {
    "en": (
        "send",
        "post",
        "upload",
        "transmit",
        "forward",
        "exfiltrate",
        "leak",
        "submit",
        "email",
        "e mail",
        "mail",
        "copy",
        "report",
        "push",
        "deliver",
        "export",
    ),
    "de": (
        r"sende(?:n)?",
        "send",
        r"schick(?:e|en)?",
        r"ubermittl?e(?:n)?",
        r"ubertrag(?:e|en)?",
        r"leite(?:n)?",
        r"lade(?:n)?",
        r"poste(?:n)?",
        r"maile(?:n)?",
        r"exportiere(?:n)?",
        r"kopiere(?:n)?",
    ),
    "fr": (
        "envoie",
        "envoyer",
        "envoyez",
        r"transmets",
        "transmettez",
        "transmettre",
        r"transfere(?:z|r)?",
        r"poste(?:z|r)?",
        r"televerse(?:z|r)?",
        r"exporte(?:z|r)?",
        r"copie(?:z|r)?",
    ),
    "it": (
        r"invia(?:re|te)?",
        r"manda(?:re|te)?",
        r"trasmetti",
        "trasmettere",
        r"inoltra(?:re|te)?",
        r"carica(?:re|te)?",
        r"spedisci",
        "spedire",
        r"esporta(?:re|te)?",
        r"copia(?:re|te)?",
    ),
}

# Starke Hinweise auf schützenswerte Inhalte (Gesprächsverlauf, Zugangsdaten, Personendaten).
SENSITIVE_NOUN: Vocab = {
    "en": (
        "conversation",
        r"chat(?: history| log| logs| transcript)?",
        r"(?:chat |conversation )?history",
        "transcript",
        "previous messages",
        "system prompt",
        "passwords?",
        "credentials?",
        r"api ?keys?",
        "secrets?",
        r"(?:access |session |auth |api )?tokens?",
        "cookies?",
        r"personal (?:data|information|details)",
        r"user s? (?:data|information|details|email address|address|phone number|name|files|messages)",
        r"customer (?:data|records|list|information|emails)",
        "contacts",
        "inbox",
        "everything",
        r"all (?:the |of the )?(?:data|information|messages|emails|files)",
        r"this (?:conversation|chat|thread)",
        "memory",
    ),
    "de": (
        r"\w{0,10}gesprach\w{0,8}",
        r"chat\w{0,10}",
        r"\w{0,10}verlauf",
        r"passw(?:o|or)rt\w{0,2}",
        r"kennw(?:o|or)rt\w{0,2}",
        "zugangsdaten",
        "anmeldedaten",
        r"api schlussel",
        r"geheimnis\w{0,2}",
        r"token\w{0,2}",
        r"(?:kunden|personen|nutzer|benutzer|kontakt|konto|lohn|patienten|mitarbeiter)\w{0,4}daten",
        r"(?:alle|samtliche) (?:daten|nachrichten|e mails|dateien)",
        "kontakte",
        "posteingang",
        "alles",
    ),
    "fr": (
        "conversation",
        r"historique(?: de la conversation)?",
        r"mots? de passe",
        "identifiants",
        r"cles? api",
        r"secrets?",
        r"jetons?",
        r"donnees (?:personnelles|des clients|de connexion|du client)",
        r"(?:toutes les|tous les) (?:donnees|messages|e mails|fichiers)",
        "contacts",
        "boite de reception",
        "tout",
    ),
    "it": (
        "conversazione",
        r"cronologia(?: della chat)?",
        "chat",
        "password",
        "credenziali",
        "chiavi api",
        "segreti",
        "token",
        r"dati (?:personali|dei clienti|di accesso|del cliente)",
        r"(?:tutti i|tutte le) (?:dati|messaggi|email|file)",
        "contatti",
        r"posta in arrivo",
        "tutto",
    ),
}

# Schwache Hinweise: alltägliche Inhalte, deren Versand nur in Dokumenten verdächtig ist.
WEAK_SENSITIVE_NOUN: Vocab = {
    "en": (
        "summary",
        "results",
        "report",
        "files",
        "documents",
        "emails",
        "messages",
        r"contents?",
        "data",
        "answer",
        "response",
    ),
    "de": (
        "zusammenfassung",
        "ergebnisse",
        "bericht",
        "dateien",
        "dokumente",
        r"e mails?",
        "nachrichten",
        r"inhalt\w{0,2}",
        "daten",
        "antwort",
    ),
    "fr": (
        "resume",
        "resultats",
        "rapport",
        "fichiers",
        "documents",
        r"e mails?",
        r"courriels?",
        r"messages?",
        "contenu",
        "donnees",
        "reponse",
    ),
    "it": (
        "riassunto",
        "risultati",
        "rapporto",
        "file",
        "documenti",
        r"e ?mail",
        "messaggi",
        "contenuto",
        "dati",
        "risposta",
    ),
}

DESTINATION: Vocab = {
    "en": ("url", "webhook", "endpoint", "server", "address", "domain", "link", "email address"),
    "de": ("url", "webhook", "endpunkt", "server", "adresse", r"e mail adresse", "domain", "link"),
    "fr": ("url", "webhook", "serveur", "adresse", "domaine", "lien"),
    "it": ("url", "webhook", "server", "indirizzo", "dominio", "link"),
}

USE_VERB: Vocab = {
    "en": ("use", "call", "invoke", "run", "execute", "trigger", "employ", "launch", "utilize"),
    "de": (
        r"nutz\w{0,2}",
        r"verwend\w{0,2}",
        r"benutz\w{0,2}",
        r"ruf\w{0,2}",
        r"fuhr\w{0,2}",
        r"start\w{0,2}",
    ),
    "fr": (
        r"utilise\w{0,2}",
        r"appelle\w{0,2}",
        r"execute\w{0,2}",
        r"lance\w{0,2}",
        r"declenche\w{0,2}",
    ),
    "it": (
        r"usa\w{0,2}",
        r"utilizza\w{0,2}",
        r"chiama\w{0,2}",
        r"esegui\w{0,2}",
        r"avvia\w{0,2}",
        r"lancia\w{0,2}",
    ),
}

TOOL_NOUN: Vocab = {
    "en": (
        r"tools?",
        r"functions?",
        r"plugins?",
        "shell",
        "terminal",
        "command line",
        "browser",
        "api",
        "code interpreter",
        "connector",
        "integration",
        "extension",
    ),
    "de": (
        r"\w{0,12}tool",
        r"\w{0,12}werkzeug",
        r"\w{0,12}funktion",
        r"\w{0,12}befehl",
        "plugin",
        "shell",
        "terminal",
        "browser",
        "schnittstelle",
        "konnektor",
    ),
    "fr": (
        r"outils?",
        r"fonctions?",
        r"commandes?",
        "plugin",
        "navigateur",
        "terminal",
        "connecteur",
    ),
    "it": (
        r"strument[oi]",
        r"funzion[ei]",
        r"comand[oi]",
        "plugin",
        "browser",
        "terminale",
        "connettore",
    ),
}

DESTRUCTIVE: Vocab = {
    "en": (
        "delete",
        "deletes",
        "remove",
        "wipe",
        "erase",
        "purge",
        "destroy",
        "drop",
        "truncate",
        "overwrite",
        "transfer",
        "wire",
        "send",
        "forward",
        "exfiltrate",
        "upload",
        "pay",
        "grant",
        "revoke",
        "disable",
        "deactivate",
        "turn off",
        "shut down",
        "reset",
        "install",
        "log into",
        "approve",
        "push",
    ),
    "de": (
        r"losch\w{0,3}",
        r"entfern\w{0,3}",
        r"vernicht\w{0,3}",
        r"uberschreib\w{0,3}",
        r"uberweis\w{0,3}",
        r"send\w{0,3}",
        r"weiterleit\w{0,3}",
        r"hochlad\w{0,3}",
        r"zahl\w{0,3}",
        r"deaktivier\w{0,3}",
        r"abschalt\w{0,3}",
        r"zurucksetz\w{0,3}",
        r"installier\w{0,3}",
        r"freigeb\w{0,3}",
        r"genehmig\w{0,3}",
    ),
    "fr": (
        r"supprim\w{0,3}",
        r"effac\w{0,3}",
        r"detrui\w{0,3}",
        r"transfer\w{0,3}",
        r"vire\w{0,2}",
        r"envoy\w{0,3}",
        "envoie",
        r"desactiv\w{0,3}",
        r"install\w{0,3}",
        r"approuv\w{0,3}",
    ),
    "it": (
        r"cancell\w{0,4}",
        r"elimin\w{0,4}",
        r"distrugg\w{0,4}",
        r"trasferi\w{0,4}",
        r"invia\w{0,3}",
        r"inoltra\w{0,3}",
        r"disattiv\w{0,4}",
        r"install\w{0,4}",
        r"approva\w{0,3}",
        r"paga\w{0,3}",
    ),
}

AI_NOUN: Vocab = {
    "en": (
        "ai",
        "a i",
        "assistant",
        "assistants",
        "llm",
        "llms",
        "chatbot",
        "chatbots",
        "bot",
        "bots",
        "language model",
        "model",
        "copilot",
        "agent",
        "agents",
        "gpt",
        "chatgpt",
        "ai assistant",
        "ai model",
        "coding agent",
    ),
    "de": (
        "ki",
        r"ki assistent\w{0,2}",
        r"ki system\w{0,2}",
        r"assistent\w{0,2}",
        r"sprachmodell\w{0,2}",
        r"agentensystem\w{0,2}",
        r"bewertungssystem\w{0,2}",
        r"\w{0,12}system\w{0,2}",
        "bot",
    ),
    "fr": (
        "ia",
        "l ia",
        "assistant",
        "assistant ia",
        r"modele\w{0,2}(?: de langage)?",
        "agent",
        "chatbot",
        "robot",
    ),
    "it": (
        "ia",
        "l ia",
        "agente",
        "assistente",
        "assistente ia",
        r"modell[oi](?: linguistic[oi])?",
        "chatbot",
    ),
}

NOTE_WORD: Vocab = {
    "en": (
        "note",
        "notes",
        "message",
        "instruction",
        "instructions",
        "attention",
        "important",
        "reminder",
    ),
    "de": (
        "hinweis",
        "nachricht",
        "anweisung",
        "anweisungen",
        "achtung",
        "wichtig",
        "info",
        "mitteilung",
    ),
    "fr": (
        "remarque",
        "note",
        "message",
        "instruction",
        "instructions",
        "attention",
        "important",
        "consigne",
    ),
    "it": (
        "nota",
        "messaggio",
        "istruzioni",
        "istruzione",
        "attenzione",
        "importante",
        "avviso",
        "indicazioni",
    ),
}

# Schlüsselwörter für die Reparatur-Sichten (Buchstabendreher, zerteilte Wörter).
# Nur Wörter, die in Angriffen zentral sind; bewusst kurz gehalten, um Fehlalarme zu vermeiden.
KEY_WORDS = frozenset(
    """
    ignore disregard forget override bypass previous prior above earlier instructions instruction
    rules guidelines directives system prompt reveal print repeat config configuration password
    passwords secret secrets developer jailbreak unrestricted unfiltered uncensored restrictions
    filters conversation history everything verbatim
    ignoriere ignorieren vergiss vergessen missachte vorherigen vorherige bisherigen obigen
    anweisungen anweisung instruktionen regeln vorgaben richtlinien systemprompt zeige verrate
    wiederhole entwicklermodus einschrankungen passwort gesprachsverlauf chatverlauf
    ignorez oublie oubliez precedentes precedents consignes regles systeme revele affiche montre
    repete historique
    ignora dimentica precedenti istruzioni regole sistema rivela mostra ripeti restrizioni
    cronologia
    """.split()
)

_ALL_VOCABS: tuple[Vocab, ...] = (
    OVERRIDE_VERB,
    QUALIFIER,
    SECOND_PERSON,
    POST_QUALIFIER,
    INSTRUCTION_NOUN,
    SAFETY_NOUN,
    DISABLE_VERB,
    FILTER_NOUN,
    PERSONA_FRAME,
    UNRESTRICTED,
    JAILBREAK_MODE,
    PRIVILEGED_MODE,
    MODE_ACTIVATION,
    MODE_STATE,
    LEAK_VERB,
    LEAK_QUESTION,
    SYSTEM_PROMPT_NOUN,
    SEND_VERB,
    SENSITIVE_NOUN,
    WEAK_SENSITIVE_NOUN,
    DESTINATION,
    USE_VERB,
    TOOL_NOUN,
    DESTRUCTIVE,
    AI_NOUN,
    NOTE_WORD,
)

# Wörter, die auch ausserhalb der Regelwortschätze eindeutig eine Sprache anzeigen.
_EXTRA_MARKERS: Mapping[str, tuple[str, ...]] = {
    "en": ("the", "and", "please", "now", "from", "with", "to", "this", "of"),
    "de": (
        "und",
        "der",
        "die",
        "das",
        "bitte",
        "mir",
        "jetzt",
        "ab",
        "sofort",
        "nicht",
        "zu",
        "dem",
    ),
    "fr": ("et", "les", "le", "moi", "maintenant", "desormais", "sans", "pour", "de", "des", "du"),
    "it": ("il", "gli", "mi", "ora", "adesso", "senza", "per", "di", "della", "delle", "dei"),
}


@functools.lru_cache(maxsize=1)
def _token_patterns() -> dict[str, re.Pattern[str]]:
    per_lang: dict[str, set[str]] = {lang: set() for lang in LANGUAGES}
    for vocab in _ALL_VOCABS:
        for lang, entries in vocab.items():
            for entry in entries:
                if "(" in entry:
                    # Zusammengesetzte Ausdrücke nur über ihre einfachen Teile zuordnen.
                    parts = re.findall(r"[a-z]{3,}", entry)
                    per_lang[lang].update(parts)
                else:
                    per_lang[lang].update(part for part in re.split(r" \?| ", entry) if part)
    for lang, markers in _EXTRA_MARKERS.items():
        per_lang[lang].update(markers)
    return {
        lang: re.compile("(?:" + "|".join(sorted(tokens, key=len, reverse=True)) + r")\Z")
        for lang, tokens in per_lang.items()
    }


def attribute_language(folded_text: str) -> str:
    """Ordnet einen (gefalteten) Treffer einer Sprache zu.

    Rückgabe ``de``/``fr``/``it``/``en``, ``mixed`` bei eindeutigen Wörtern aus mehreren
    Sprachen oder ``any``, wenn kein Wort eindeutig ist (z.B. ``<|im_start|>``).
    """
    patterns = _token_patterns()
    counts: dict[str, int] = {}
    for token in re.findall(r"[^\W_]+", folded_text):
        hits = [lang for lang, pattern in patterns.items() if pattern.match(token)]
        if len(hits) == 1:
            counts[hits[0]] = counts.get(hits[0], 0) + 1
    if not counts:
        return "any"
    if len(counts) == 1:
        return next(iter(counts))
    ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    if ranked[1][1] >= 1 and ranked[0][1] < 3 * ranked[1][1]:
        return "mixed"
    return ranked[0][0]
