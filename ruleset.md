### Ruleset

#### Character Creation
- **Stats**: Each character has four primary ability scores (ranging from 1 to 20, where 10 is average):
	- **Magical Prowess (MP)**: Innate magical talent and spellcasting ability. Modifier = `floor((MP - 10) / 2)`.
	- **Physical Prowess (PP)**: Strength, agility, and physical resilience. Modifier = `floor((PP - 10) / 2)`.
	- **Mental Acuity (MA)**: Intelligence, perception, and magical intuition for knowledge and investigation. Modifier = `floor((MA - 10) / 2)`.
	- **Social Grace (SG)**: Charisma, persuasion, and social interactions, including certain enchantment spells. Modifier = `floor((SG - 10) / 2)`.
- **Proficiencies**: Skills tied to each stat, reflecting Hogwarts education and wizarding life:
	- **MP**: Charms, Transfiguration, Potions, Standard spells, Curses, Jinxes, Nonverbal Casting
	- **PP**: Flying, Dueling, Stealth, Elemental spells.
	- **MA**: History of Magic, Arithmancy, Ancient Runes, Herbology, Healing spells, Investigation, Perception.
	- **SG**: Persuasion, Deception, Intimidation, Performance, Enchantment spells.
	- **Starting Proficiencies**: At character creation (Year 1), choose **two** proficiencies based on character background/aptitude. Gain **one** additional proficiency based on your chosen House (e.g., Gryffindor might grant Dueling, Ravenclaw History of Magic, Hufflepuff Herbology, Slytherin Deception - GM decides or provides options). You gain additional proficiencies as you progress through years.
- **House**: Choose Gryffindor, Hufflepuff, Ravenclaw, or Slytherin. Each provides unique abilities (see Section 11).
- **Year**: Select Year 1–7, influencing starting abilities, proficiency bonus, and Magical Stamina.
- **Magical Stamina (MS)**: Pool = `10 + (Year × 2) + MP Modifier`. Depletes with spellcasting; recharges via rest or potions.
- **Hit Points (HP)**: Pool = `10 + (Year × 2) + PP Modifier`. Represents physical health.
- **Starting Spells**: Based on year (see Section 8).

#### House Abilities
Each house provides two special abilities - one at Year 1 and another at Year 4.

##### Gryffindor Abilities
- **Year 1: Heroic Surge**: Once per long rest, gain temporary MS equal to `Year + Proficiency Bonus`. This bonus MS disappears after 10 minutes or 5 turns. If you end up with less than 0 MS, you faint for an hour.
- **Year 4: Swish and Flick**: Once per combat, you may cast two offensive spells in a single action.

##### Hufflepuff Abilities
- **Year 1: True Friend**: When you use the Help action to aid an ally's check, they gain a +2 bonus to their roll in addition to Advantage.
- **Year 4: Perseverance**: When at 0 MS, you can still attempt to cast a spell by taking 1d4 Hit Point damage, adding 1d4 for each spell difficulty category.

##### Ravenclaw Abilities
- **Year 1: Quick Study**: Reduce the required downtime or number of checks needed to learn a new spell or proficiency through Personal Study by one step (GM discretion on specifics).
- **Year 4: Eureka Moment**: Once per long rest, you can choose to succeed on one MA-based skill check (Investigation, History of Magic, Arithmancy, Ancient Runes, Perception) as if you had rolled a natural 20.

##### Slytherin Abilities
- **Year 1: Cunning**: Once per long rest, you can reroll any SG-based check (Persuasion, Deception, Intimidation).
- **Year 4: Resourceful Magic**: Once per long rest, you may attempt to cast any one spell you have seen successfully cast within the last 24 hours, even if it is not in your spellbook. You must still meet the MS cost and make the spellcasting check (potentially at Disadvantage if it's far above your level).

#### Dice Mechanics
- **Checks**: Roll a d20 + relevant stat modifier + proficiency bonus (if proficient) vs. a Difficulty Class (DC) to determine success.
- **Proficiency Bonus**: Increases with year:
	- Year 1: +0
	- Year 2–3: +1
	- Year 4–6: +2
	- Year 7: +3
- **Spellcasting**: To cast a spell, roll d20 + MP modifier + proficiency bonus (if proficient in the spell’s category) vs. the spell’s DC. MS cost is spent regardless of success or failure.
- **Saving Throws**: When targeted by a spell or effect requiring resistance, roll d20 + relevant stat modifier (specified by the spell/effect) vs. the caster's Spell Save DC (`8 + Caster's MP Modifier + Caster's Proficiency Bonus`) or a set DC for environmental effects.

#### Hit Points and Physical Health
- **Taking Damage**: HP is reduced by attacks, hazards, or certain strenuous activities (like Hufflepuff's Perseverance).
- **Critical State**: At 0 HP, a character falls unconscious and is incapacitated. Further damage while unconscious may lead to death (GM discretion or specific rules for lasting injuries).
- **Recovery**:
	- **Short Rest** (1 hour): Regain HP equal to `2d6 + PP Modifier`.
	- **Long Rest** (8 hours): Regain all lost HP.
- **Healing Magic**: Spells like *Episkey* restore HP as described in the spellbook. Stabilizing a character at 0 HP typically requires a successful MA check (DC 10) or a healing spell.

#### Spell Mechanics
- **Spell Difficulty & Cost**: Spells are categorized with corresponding DCs and MS costs:
	- **Basic**: DC 10, **1 MS** (e.g., *Lumos*, *Incendio*)
	- **Intermediate**: DC 15, **3 MS** (e.g., *Expelliarmus*, *Reducto*)
	- **Advanced**: DC 20, **5 MS** (e.g., *Expecto Patronum*, *Confringo*)
	- **Expert**: DC 25, **7 MS** (e.g., *Avada Kedavra*, *Fiendfyre*)
- **Categories**: Spells align with proficiencies (granting proficiency bonus to the casting roll if applicable).
- **Special Requirements**: Some spells need conditions (e.g., *Expecto Patronum* requires focus on a happy memory, potentially requiring a separate check like MA DC 10 under stress).
- **Magical Stamina Management**:
	- MS depletes with each spell cast.
	- At 0 MS, no spells requiring MS can be cast (unless an ability like Hufflepuff's Perseverance allows it).
	- **Recharge**:
		- **Short Rest** (1 hour): Regain MS equal to `Year + MP Modifier + Proficiency Bonus`. (This scales better with higher costs).
		- **Long Rest** (8 hours): Regain full MS pool.
		- **Potions**: Specific potions (e.g., Pepperup Potion) might restore MS (e.g., DC 15 Potions check to brew, restores 1d6+1 MS upon consumption).

#### Damage Types, Resistances, and Vulnerabilities
- **Damage Types**: *Fire*, *Force*, *Cold*, *Radiant*, *Psychic*, *Slashing*, *Piercing*, *Bludgeoning* (for physical).
- **Resistance**: Creature takes **half damage** from that type.
- **Vulnerability**: Creature takes **double damage** from that type.
- **Immunity**: Creature takes **no damage** from that type.
- **Sample Traits**: Inferi (Vulnerable: Fire, Immune: Cold, Piercing); Ghosts (Immune: Physical, Force); Trolls (Resistant: Slashing, Bludgeoning). The GM determines these for NPCs/creatures.

#### Nonverbal Spellcasting
Nonverbal spellcasting involves performing magic without speaking the incantation aloud, requiring significant concentration and magical control.

- **Requirements**:
  - Attempting nonverbal casting is typically only feasible for students in **Year 6 or higher**, reflecting the advanced skill required.
  - The GM might allow exceptionally gifted students (e.g., high MP score of 16+) to attempt it earlier under specific circumstances or with mentorship.

- **Mechanics**:
  - When attempting to cast a known spell nonverbally, the **Spellcasting DC increases by 8**.
  - However, if the chracter is proficient in Nonverbal Spellcasting **Spellcasting DC only increases by 5**.
  - The MS cost for the spell remains the same as its verbal counterpart.
  - The caster makes the standard spellcasting check: `d20 + MP Modifier + Proficiency Bonus (if applicable)` vs. the **new, higher DC**.

- **Benefits**:
  - **Stealth**: Allows casting spells without revealing intent through spoken words, useful for ambushes or subtle magic.
  - **Circumvention**: Enables casting when silenced or otherwise unable to speak, provided the spell doesn't also require gestures that are restricted.

#### Combat and Dueling
- **Initiative**: All participants roll d20 + PP modifier at the start of combat. Highest roll goes first, then descending order. Ties broken by highest PP score, then coin flip/GM decision.
- **Actions**: On your turn, you can take **one Action** (e.g., Cast a Spell, Attack, Use an Object, Dash, Disengage, Dodge, Help) and **move** up to your speed (typically 30 feet). Some spells or abilities might use a Bonus Action or Reaction if specified.
- **Offensive Spells**: Caster makes a spellcasting check (d20 + MP Mod + Prof Bonus vs Spell DC). If successful, the spell takes effect. If the spell requires a save, the target makes a saving throw against the caster's Spell Save DC (`8 + Caster MP Mod + Caster Prof Bonus`). Failure means suffering the spell's effects.
- **Defensive Spells**: Spells like *Protego* are cast as an Action (or Reaction if specified). They might negate an incoming spell/attack if the caster's spellcasting check meets or exceeds the incoming attack roll or spell save DC, or provide a temporary HP shield, as described by the spell.

#### Other Activities
- **Potions**: Brewing requires ingredients and a check (d20 + MP modifier + Potions proficiency bonus) vs. the potion's DC. Consuming a potion is typically an Action.
- **Quidditch**: Involves a series of checks using PP (Flying, Dodging), MA (Perception for Seekers, tactical awareness), and potentially SG (team coordination/intimidation) depending on the situation and position.
- **Social**: Interactions like Persuasion, Deception, Intimidation use d20 + SG modifier + relevant proficiency bonus vs. the target's passive MA or SG, or an actively rolled contest (e.g., Insight vs Deception).

#### Progression
- **Advancement**: Progress through Hogwarts years is achieved via story milestones (typically end-of-year events). Upon advancing a year:
	- Increase **one** ability score of your choice by +1 (maximum 20).
	- Gain **one** new proficiency of your choice.
	- Learn new spells automatically (see Section 8).
	- Increase MS and HP pools based on the Year component of their formulas.
	- Proficiency Bonus increases at Years 2, 4, and 7.

#### Spell Acquisition
- **Automatic Learning**: At the start of each new Hogwarts year, characters automatically learn a number of spells appropriate to their curriculum.
	- **Start of Year 1**: Learn **3 Basic** spells.
	- **Start of Year 2**: Learn **2 Intermediate** spells.
	- **Start of Year 3**: Learn **1 Intermediate** and **1 Advanced** spell.
	- **Start of Year 4**: Learn **2 Advanced** spells.
	- **Start of Year 5**: Learn **1 Advanced** and **1 Expert** spell.
	- **Start of Year 6**: Learn **2 Expert** spells.
	- **Start of Year 7**: Learn **1 Expert** spell and gain **one** additional spell of choice up to Advanced level.
	- Spells chosen must be from lists generally considered appropriate for that year level (GM guidance).
- **Additional Learning**: Spells beyond the automatic ones can be learned through:
	- **Classes**: Exceptional success on assignments or practical exams (e.g., MA check DC 18).
	- **Mentorship**: Dedicated teaching from professors or skilled peers (requires time and potential checks).
	- **Personal Study**: Researching in the library or practicing (requires downtime and successful checks, e.g., DC 15+ Investigation to find, then practice time and potentially MP checks).
	- **Discovery**: Finding spellbooks, scrolls, or ancient texts during adventures.
- **Limitations**: Generally, characters cannot learn spells significantly above their Year level unless specific narrative circumstances (e.g., prodigy, unique discovery) and GM permission allow it. Casting spells above one's typical Year level might incur Disadvantage on the roll or increased MS cost.

#### Transfiguration Rules
- **Impermanence**: Transfigurations are not permanent and eventually revert. Reversion inside a living being is dangerous/lethal. Sustaining requires periodic re-application of magic.
- **MS Costs & Checks**:
    - Simple (matchstick to needle): **1 MS**, DC 10 MP Check.
	- Moderate (stool to badger): **3 MS**, DC 15 MP Check.
	- Complex / Living (goblet to bird): **5 MS**, DC 20 MP Check.
- Failure results in partial, unstable, or failed transformation. Human transfiguration is extremely advanced and dangerous (Expert level difficulty, high DCs, potential severe consequences on failure).

#### Example simplified character sheets
##### Character: Red Cap
- **Estimated Level Equiv:** Year 2 (Proficiency Bonus: +1)
- **Stats:**
    - MP: 6 (-2)
    - PP: 14 (+2)
    - MA: 8 (-1)
    - SG: 5 (-3)
- **HP:** 16
- **AC:** 12 (Base 10 + PP Modifier)
- **MS:** N/A (Does not use magical stamina)
- **Attack:** Club - Attack Bonus: +3 (`d20 + PP Mod + Prof Bonus`), Damage: 1d6+2 Bludgeoning.
- **Noteworthy Abilities:**
    - *Aggressive*: Prefers direct melee combat.
    - *Weakness (Charms)*: Has Disadvantage on Saving Throws against charm spells that directly target it (like *Flipendo*, *Immobulus*, but not AoE like *Incendio*).
    - *Shadow Lurker*: Has Proficiency in Stealth (+3 Bonus: `d20 + PP Mod + Prof Bonus`).

##### Character: Alastor "Mad-Eye" Moody
- **Estimated Level Equiv:** 7+ (Proficiency Bonus: +3)
- **Stats:**
    - MP: 18 (+4)  # Highly skilled caster
    - PP: 16 (+3)  # Experienced duelist, tough
    - MA: 20 (+5)  # Legendary perception & paranoia
    - SG: 9 (-1)   # Gruff and direct
- **HP:** 75      # Veteran Auror resilience
- **MS:** 35      # Solid pool for sustained combat/utility
- **Spell Save DC:** 15 (`8 + 4 MP Mod + 3 Prof Bonus`)
- **Noteworthy Abilities:**
    - *Magical Eye*: Grants 360-degree vision. Can see through solid objects (wood, cloth, standard walls), Invisibility Cloaks, and automatically detect most magical disguises or enchantments within 60 ft. Grants Advantage on all Perception checks.
    - *CONSTANT VIGILANCE!*: Cannot be surprised. Gains Advantage on Initiative rolls.
    - *Master Duelist*: Proficient in Dueling (+3). Can cast *Protego* (Basic version) as a Reaction once per round by spending 1 MS.
    - *Auror Veteran*: Has Advantage on Saving Throws against Curses and mind-affecting spells (*Imperio*, *Confundo*, *Legilimens*). Proficient in Investigation (+8), Perception (+8).
    - *Non-Verbal Casting*: Can cast known spells up to Advanced difficulty without verbal components.
    - *Likely Known Spells*: Assumed to know a wide range of offensive (Stunning, Disarming, Binding), defensive (*Protego variants*), and utility spells (*Homenum Revelio* etc.) appropriate for a top Auror.