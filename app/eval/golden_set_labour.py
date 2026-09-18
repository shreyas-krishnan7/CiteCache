"""
Golden set for the Indian labour-law corpus in data/docs_labour/:
the Occupational Safety, Health and Working Conditions Code, 2020;
the Code on Wages, 2019; and the Bonded Labour System (Abolition)
Act, 1976.

Every reference_answer below is taken from the section cited in the
comment alongside it, so RAGAS's ground-truth metrics
(context_recall, factual_correctness) score against the statute text
rather than against a paraphrase.

expected_source values are the ingested file stems, so they only match
if data/docs_labour was ingested with those filenames.
"""
from __future__ import annotations

from app.eval.golden_set import GoldenQuestion

OSH = "osh_code_2020"
WAGES = "code_on_wages_2019"
BONDED = "bonded_labour_act_1976"


GOLDEN_SET: list[GoldenQuestion] = [
    # ---------- Bonded Labour System (Abolition) Act, 1976 ----------
    GoldenQuestion("b01", "What is the punishment for compelling a person to render bonded labour?",
                   True, BONDED, ["three years", "two thousand"],
                   "Under section 16, whoever compels any person to render bonded labour after the "
                   "commencement of the Act is punishable with imprisonment for a term which may "
                   "extend to three years and also with fine which may extend to two thousand rupees."),
    GoldenQuestion("b02", "Who bears the burden of proof when a debt is claimed to be a bonded debt?",
                   True, BONDED, ["creditor", "burden"],
                   "Section 15 places the burden on the creditor. Whenever a bonded labourer or a "
                   "Vigilance Committee claims that a debt is a bonded debt, the burden of proving "
                   "that it is not a bonded debt lies on the creditor."),
    GoldenQuestion("b03", "What happened to bonded debts when the Act came into force?",
                   True, BONDED, ["extinguished"],
                   "Under section 6, every obligation of a bonded labourer to repay a bonded debt was "
                   "deemed extinguished on commencement of the Act. No suit or proceeding for recovery "
                   "of a bonded debt lies in any civil court, pending suits stood dismissed, unsatisfied "
                   "decrees were deemed fully satisfied, and any bonded labourer detained in civil "
                   "prison was to be released forthwith."),
    GoldenQuestion("b04", "Can a freed bonded labourer be evicted from their homestead?",
                   True, BONDED, ["evicted", "executive magistrate"],
                   "No. Section 8 bars eviction of a freed bonded labourer from any homestead or other "
                   "residential premises he occupied as part of the consideration for the bonded labour. "
                   "If the creditor does evict him, the Executive Magistrate in charge of the Sub-Division "
                   "must restore him to possession as early as practicable."),
    GoldenQuestion("b05", "Who chairs a district Vigilance Committee and how many members must belong "
                          "to the Scheduled Castes or Scheduled Tribes?",
                   True, BONDED, ["district magistrate", "three"],
                   "Under section 13(2), the District Magistrate or a person nominated by him is the "
                   "Chairman. Three members must be persons belonging to the Scheduled Castes or "
                   "Scheduled Tribes who reside in the district, nominated by the District Magistrate."),
    GoldenQuestion("b06", "What is the penalty if a creditor accepts payment against a debt that has "
                          "already been extinguished?",
                   True, BONDED, ["three years"],
                   "Section 9 prohibits a creditor from accepting any payment against an extinguished "
                   "bonded debt. Contravention is punishable with imprisonment for a term which may "
                   "extend to three years and also with fine, and the convicting court may additionally "
                   "direct the person to deposit the amount accepted in court for refund to the bonded "
                   "labourer."),
    GoldenQuestion("b07", "When is the Bonded Labour System (Abolition) Act deemed to have come into force?",
                   True, BONDED, ["25th day of october, 1975"],
                   "Although the Act is Act No. 19 of 1976 and received assent on 9th February 1976, "
                   "section 1(3) provides that it shall be deemed to have come into force on the 25th "
                   "day of October, 1975, the day after the Ordinance it replaced was promulgated."),
    GoldenQuestion("b08", "What is the punishment for abetting an offence under the Bonded Labour "
                          "System (Abolition) Act?",
                   True, BONDED, ["same punishment"],
                   "Under section 20, whoever abets any offence punishable under the Act is punishable "
                   "with the same punishment as is provided for the offence abetted, whether or not the "
                   "offence abetted is actually committed."),

    # ---------- Code on Wages, 2019 ----------
    GoldenQuestion("w01", "What is the overtime rate under the Code on Wages?",
                   True, WAGES, ["twice"],
                   "Section 14 provides that where an employee works in excess of the hours "
                   "constituting a normal working day, the employer must pay for every hour or part of "
                   "an hour worked in excess at an overtime rate which shall not be less than twice the "
                   "normal rate of wages."),
    GoldenQuestion("w02", "By when must an employer pay wages to a monthly-paid employee?",
                   True, WAGES, ["seventh day"],
                   "Section 17(1)(iv) requires wages for employees engaged on a monthly basis to be "
                   "paid before the expiry of the seventh day of the succeeding month. Daily-paid "
                   "employees must be paid at the end of the shift, weekly-paid before the weekly "
                   "holiday, and fortnightly-paid before the end of the second day after the fortnight."),
    GoldenQuestion("w03", "When must wages be paid to an employee who has been dismissed or has resigned?",
                   True, WAGES, ["two working days"],
                   "Section 17(2) requires that where an employee is removed, dismissed, retrenched, "
                   "resigns, or becomes unemployed due to closure of the establishment, the wages "
                   "payable must be paid within two working days."),
    GoldenQuestion("w04", "What is the maximum total deduction that can be made from an employee's "
                          "wages in a wage period?",
                   True, WAGES, ["fifty per cent"],
                   "Section 18(3) caps total deductions in any wage period at fifty per cent of the "
                   "employee's wages for that period. Where authorised deductions exceed fifty per cent, "
                   "section 18(4) provides that the excess may be recovered in the prescribed manner."),
    GoldenQuestion("w05", "What limits apply to fines imposed on an employee, and can a 14-year-old "
                          "be fined?",
                   True, WAGES, ["three per cent", "fifteen years"],
                   "Under section 19, the total fine imposed in any one wage period cannot exceed three "
                   "per cent of the wages payable for that wage period, and no fine may be recovered in "
                   "instalments or after ninety days from the day it was imposed. A 14-year-old cannot "
                   "be fined at all, because section 19(5) bars imposing any fine on an employee under "
                   "the age of fifteen years."),
    GoldenQuestion("w06", "What is the minimum bonus payable under the Code on Wages?",
                   True, WAGES, ["eight and one-third per cent", "one hundred rupees", "thirty days"],
                   "Section 26(1) entitles an employee who has put in at least thirty days work in an "
                   "accounting year to an annual minimum bonus of eight and one-third per cent of the "
                   "wages earned or one hundred rupees, whichever is higher, payable whether or not the "
                   "employer has any allocable surplus. Where the allocable surplus is larger, bonus is "
                   "paid in proportion to wages earned, subject to a maximum of twenty per cent."),
    GoldenQuestion("w07", "Within what time must bonus be paid?",
                   True, WAGES, ["eight months"],
                   "Section 39(1) requires all bonus to be credited to the employee's bank account "
                   "within eight months from the close of the accounting year. The appropriate "
                   "Government may, on the employer's application and for sufficient reasons, extend "
                   "that period, but the total extended period cannot exceed two years."),
    GoldenQuestion("w08", "What disqualifies an employee from receiving bonus?",
                   True, WAGES, ["fraud", "sexual harassment"],
                   "Section 29 disqualifies an employee who is dismissed from service for fraud, for "
                   "riotous or violent behaviour while on the premises of the establishment, for theft, "
                   "misappropriation or sabotage of any property of the establishment, or for conviction "
                   "for sexual harassment."),
    GoldenQuestion("w09", "What is the time limit for filing a claim under the Code on Wages?",
                   True, WAGES, ["three years"],
                   "Section 45(6) allows an application to be filed within three years from the date on "
                   "which the claim arises, though the authority may entertain a later application if "
                   "sufficient cause for the delay is shown. The authority may also award compensation "
                   "up to ten times the claim determined and is to endeavour to decide the claim within "
                   "three months."),
    GoldenQuestion("w10", "What is the penalty for an employer who pays an employee less than the "
                          "amount due, and what happens on a repeat offence?",
                   True, WAGES, ["fifty thousand", "one lakh", "three months"],
                   "Under section 54(1)(a) an employer who pays less than the amount due is punishable "
                   "with fine which may extend to fifty thousand rupees. If convicted again of a similar "
                   "offence within five years, section 54(1)(b) provides for imprisonment which may "
                   "extend to three months or fine which may extend to one lakh rupees, or both."),
    GoldenQuestion("w11", "How often must minimum wages be reviewed or revised?",
                   True, WAGES, ["five years"],
                   "Section 8(4) requires the appropriate Government to review or revise minimum rates "
                   "of wages ordinarily at an interval not exceeding five years."),
    GoldenQuestion("w12", "Is house rent allowance included in 'wages' under the Code on Wages?",
                   True, WAGES, ["house rent allowance", "one-half"],
                   "Generally no. The definition in section 2(y) includes basic pay, dearness allowance "
                   "and retaining allowance, and expressly excludes house rent allowance. Two provisos "
                   "qualify this: if the excluded payments in clauses (a) to (i) exceed one-half of all "
                   "remuneration, the excess is deemed remuneration and added back into wages; and for "
                   "the purposes of equal wages across genders and of payment of wages, house rent "
                   "allowance is taken into computation."),
    GoldenQuestion("w13", "Can an offence under the Code on Wages be compounded, and at what cost?",
                   True, WAGES, ["fifty per cent"],
                   "Section 56 allows any offence not punishable with imprisonment only, or with "
                   "imprisonment and also fine, to be compounded by a notified Gazetted Officer for a "
                   "sum of fifty per cent of the maximum fine provided for that offence. Compounding is "
                   "unavailable to a person who commits a similar offence a second time within five "
                   "years of an earlier compounding or conviction."),
    GoldenQuestion("w14", "Who is excluded from the definition of 'worker' under the Code on Wages?",
                   True, WAGES, ["fifteen thousand"],
                   "Section 2(z) excludes members of the Air Force, Army and Navy, persons employed in "
                   "the police service or as an officer or employee of a prison, persons employed mainly "
                   "in a managerial or administrative capacity, and persons employed in a supervisory "
                   "capacity drawing wages exceeding fifteen thousand rupees per month or such other "
                   "amount as the Central Government may notify."),

    # ---------- Occupational Safety, Health and Working Conditions Code, 2020 ----------
    GoldenQuestion("o01", "How many hours a day and days a week can a worker be required to work "
                          "under the OSH Code?",
                   True, OSH, ["eight hours", "six days"],
                   "Section 25(1) bars requiring or allowing a worker to work more than eight hours in "
                   "a day, with the daily period fixed so as not to exceed the hours, intervals and "
                   "spread-overs notified by the appropriate Government. Section 26(1) additionally "
                   "bars work on more than six days in any one week."),
    GoldenQuestion("o02", "What overtime rate applies under the OSH Code and is the worker's consent "
                          "required?",
                   True, OSH, ["twice", "consent"],
                   "Section 27 requires wages at twice the rate of wages for overtime work beyond the "
                   "hours prescribed by the appropriate Government, with the overtime period calculated "
                   "on a daily or weekly basis, whichever is more favourable to the worker. A worker may "
                   "be required to work overtime only with that worker's consent."),
    GoldenQuestion("o03", "How much annual leave with wages is a worker entitled to under the OSH Code?",
                   True, OSH, ["one hundred and eighty days", "twenty days", "thirty days"],
                   "Under section 32(1), a worker who has worked one hundred and eighty days or more in "
                   "a calendar year earns one day of leave for every twenty days worked. The rate is one "
                   "day for every fifteen days for an adolescent worker and for a worker employed below "
                   "ground in a mine. Untaken leave carries forward subject to a cap of thirty days, "
                   "leave that was applied for and refused carries forward without limit, and the worker "
                   "may demand encashment at the end of the calendar year."),
    GoldenQuestion("o04", "When must an employer appoint a safety officer?",
                   True, OSH, ["five hundred", "two hundred fifty", "one hundred"],
                   "Section 22(2) requires safety officers in a factory where five hundred or more "
                   "workers are ordinarily employed, a factory carrying on a hazardous process with two "
                   "hundred fifty or more workers, building or other construction work with two hundred "
                   "fifty or more workers, and a mine with one hundred or more workers."),
    GoldenQuestion("o05", "When is a canteen required, and when is a creche required?",
                   True, OSH, ["one hundred", "fifty"],
                   "Section 24(1)(v) requires a canteen in an establishment where one hundred or more "
                   "workers, including contract labourers, are ordinarily employed. Section 24(3) "
                   "provides for creche facilities for children under six years of age in establishments "
                   "where more than fifty workers are ordinarily employed, and establishments may pool "
                   "resources or use a common creche."),
    GoldenQuestion("o06", "Can women be employed at night under the OSH Code?",
                   True, OSH, ["consent", "6 a.m.", "7 p.m."],
                   "Yes. Section 43 entitles women to be employed in all establishments for all types of "
                   "work, and permits their employment before 6 a.m. and beyond 7 p.m. with their "
                   "consent, subject to conditions on safety, holidays and working hours prescribed by "
                   "the appropriate Government."),
    GoldenQuestion("o07", "Within how many days must a new establishment apply for registration?",
                   True, OSH, ["sixty days", "thirty days"],
                   "Section 3(1) requires an electronic application to the registering officer within "
                   "sixty days from the date the Code becomes applicable to the establishment; a late "
                   "application may be entertained on payment of prescribed late fees. Any later change "
                   "in ownership, management or registered particulars must be intimated within thirty "
                   "days, and closure must be intimated within thirty days of closing."),
    GoldenQuestion("o08", "When do the contract labour provisions of the OSH Code apply?",
                   True, OSH, ["fifty or more"],
                   "Under section 45(1), Part I applies to every establishment in which fifty or more "
                   "contract labour are employed, or were employed on any day of the preceding twelve "
                   "months, and to every manpower supply contractor who employed fifty or more contract "
                   "labour on any day of the preceding twelve months. It does not apply where only work "
                   "of an intermittent or casual nature is performed."),
    GoldenQuestion("o09", "What happens if a contractor fails to pay wages to contract labour?",
                   True, OSH, ["principal employer", "recover"],
                   "Section 55(3) makes the principal employer liable to pay the wages in full, or the "
                   "unpaid balance, to the contract labour concerned, and to recover that amount from "
                   "the contractor either by deduction from any sum payable to the contractor or as a "
                   "debt. The appropriate Government may also order payment out of the contractor's "
                   "security deposit."),
    GoldenQuestion("o10", "When do the inter-State migrant worker provisions apply, and what travel "
                          "benefit do such workers receive?",
                   True, OSH, ["ten or more", "journey"],
                   "Section 59 applies Part II to every establishment in which ten or more inter-State "
                   "migrant workers are employed, or were employed on any day of the preceding twelve "
                   "months. Section 61 requires the employer to pay each such worker, once a year, a "
                   "lump sum fare for the to-and-fro journey to his native place."),
    GoldenQuestion("o11", "Which accidents must be notified under the OSH Code?",
                   True, OSH, ["forty-eight hours", "death"],
                   "Section 10(1) requires notice where an accident causes death, or causes bodily "
                   "injury by reason of which the injured person is prevented from working for "
                   "forty-eight hours or more immediately following the accident, or is of such nature "
                   "as the appropriate Government prescribes. Where the notice concerns a death in a "
                   "plantation, building or other construction work or any other establishment, the "
                   "authority must inquire into the occurrence within two months of receiving it."),
    GoldenQuestion("o12", "What is the general penalty for contravening the OSH Code?",
                   True, OSH, ["two lakh", "three lakh", "two thousand"],
                   "Section 94 makes the employer or principal employer liable to a penalty of not less "
                   "than two lakh rupees, extending up to three lakh rupees. If the contravention "
                   "continues after conviction, a further penalty of up to two thousand rupees applies "
                   "for each day the contravention continues."),
    GoldenQuestion("o13", "What is the punishment when a safety contravention results in a worker's death?",
                   True, OSH, ["two years", "five lakh", "fifty per cent"],
                   "Section 103(1)(a) provides for imprisonment which may extend to two years, or a fine "
                   "of not less than five lakh rupees, or both. The court may direct that not less than "
                   "fifty per cent of the fine be given as compensation to the victim's legal heirs. "
                   "Where the contravention causes serious bodily injury instead, the punishment is "
                   "imprisonment up to one year or a fine of two to four lakh rupees, or both."),
    GoldenQuestion("o14", "What counts as a 'factory' and what counts as an 'establishment' under the "
                          "OSH Code?",
                   True, OSH, ["twenty or more", "forty or more", "ten or more"],
                   "Under section 2(w), a factory is premises where twenty or more workers work with a "
                   "manufacturing process carried on with the aid of power, or forty or more workers "
                   "where it is carried on without the aid of power, on any day of the preceding twelve "
                   "months. Under section 2(v), an establishment is generally a place where an industry, "
                   "trade, business, manufacture or occupation is carried on with ten or more workers, "
                   "and the threshold does not apply to notified hazardous or life-threatening activities."),
    GoldenQuestion("o15", "What rights does an employee have when there is imminent danger at the "
                          "workplace?",
                   True, OSH, ["imminent", "inspector-cum-facilitator"],
                   "Section 14 gives every employee the right to obtain health and safety information "
                   "from the employer and to raise inadequate safety provision with the employer, "
                   "directly or through a Safety Committee member, and with the Inspector-cum-Facilitator "
                   "if unsatisfied. On reasonable apprehension of imminent serious personal injury, death "
                   "or danger to health, the employee may notify the employer and the "
                   "Inspector-cum-Facilitator simultaneously; the employer must take immediate remedial "
                   "action if satisfied, and if not satisfied must still refer the matter to the "
                   "Inspector-cum-Facilitator, whose decision on the existence of imminent danger is final."),
    GoldenQuestion("o16", "Is employment of contract labour allowed in an establishment's core activity?",
                   True, OSH, ["core activit", "prohibited"],
                   "Section 57(1) prohibits employment of contract labour in the core activities of an "
                   "establishment. The proviso allows it where the activity is ordinarily done through a "
                   "contractor in the normal functioning of the establishment, where the activity does "
                   "not require full-time workers for the major portion of the working hours, or where "
                   "there is a sudden increase in the volume of core-activity work that must be finished "
                   "in a specified time."),

    # ---------- Cross-document (multi-hop retrieval) ----------
    GoldenQuestion("x01", "How does the Bonded Labour Act define 'nominal wages', and how does that "
                          "relate to minimum wages legislation?",
                   True, None, ["minimum wage", "locality"],
                   "Section 2(i) of the Bonded Labour System (Abolition) Act defines nominal wages as a "
                   "wage less than the minimum wage fixed by the Government for the same or similar "
                   "labour under any law in force, and, where no minimum wage has been fixed, less than "
                   "the wages normally paid for the same or similar labour to labourers in the same "
                   "locality. The Code on Wages supplies that reference point: section 5 bars paying "
                   "less than the minimum rate notified by the appropriate Government, section 6 governs "
                   "its fixation, and section 9 requires the Central Government to fix a floor wage "
                   "below which minimum rates cannot fall."),
    GoldenQuestion("x02", "Does the definition of 'contract labour' differ between the Code on Wages "
                          "and the OSH Code?",
                   True, None, ["contractor", "principal employer"],
                   "No, the two definitions are substantively the same. Section 2(g) of the Code on "
                   "Wages and section 2(m) of the OSH Code both define contract labour as a worker "
                   "deemed employed in or in connection with the work of an establishment when hired by "
                   "or through a contractor, with or without the knowledge of the principal employer, "
                   "and both include inter-State migrant workers. Both exclude a worker, other than a "
                   "part-time employee, who is regularly employed by the contractor under mutually "
                   "accepted conditions of employment and who receives periodical increments, social "
                   "security coverage and other welfare benefits."),
    GoldenQuestion("x03", "Both the Code on Wages and the OSH Code provide for overtime. Do they set "
                          "the same rate?",
                   True, None, ["twice"],
                   "Yes, both set overtime at twice the normal rate. Section 14 of the Code on Wages "
                   "requires payment at not less than twice the normal rate of wages for each hour "
                   "worked beyond a normal working day. Section 27 of the OSH Code requires wages at "
                   "twice the rate of wages for work beyond the prescribed daily or weekly hours, adds "
                   "that the overtime period is calculated on whichever of a daily or weekly basis is "
                   "more favourable to the worker, and requires the worker's consent to the overtime."),
    GoldenQuestion("x04", "Does the Bonded Labour System (Abolition) Act cover contract labour and "
                          "inter-State migrant workers?",
                   True, BONDED, ["contract labour", "inter-state migrant"],
                   "Yes. The Explanation to section 2(g), added by the Amendment Act of 1985, declares "
                   "that any system of forced or partly forced labour under which contract labour as "
                   "defined in the Contract Labour (Regulation and Abolition) Act, 1970, or an "
                   "inter-State migrant workman as defined in the Inter-State Migrant Workmen Act, 1979, "
                   "is required to render labour in the circumstances described in that clause, or is "
                   "subjected to the disabilities it lists, falls within the bonded labour system."),
    GoldenQuestion("x05", "Both Codes make company officers liable for offences. What must be proved "
                          "against a director?",
                   True, None, ["consent", "connivance", "neglect"],
                   "Under section 55 of the Code on Wages and section 109 of the OSH Code, the person "
                   "in charge of and responsible to the company for the conduct of its business is "
                   "deemed guilty along with the company. A director, manager, secretary or other "
                   "officer is additionally liable only where the offence is proved to have been "
                   "committed with that officer's consent or connivance, or to be attributable to that "
                   "officer's neglect. Section 23 of the Bonded Labour System (Abolition) Act applies "
                   "the same test."),

    # ---------- Out-of-corpus: correct behaviour is insufficient_context=True ----------
    # Each is adjacent to the corpus but its answer lives in a statute that is not ingested.
    GoldenQuestion("n01", "What is the current national floor wage in rupees per day?", False),
    GoldenQuestion("n02", "How many weeks of paid maternity leave is a woman worker entitled to?", False),
    GoldenQuestion("n03", "What is the employer's contribution rate to the Employees' Provident Fund?", False),
    GoldenQuestion("n04", "How is gratuity calculated on termination of employment?", False),
    GoldenQuestion("n05", "What is the procedure for filing a sexual harassment complaint at the workplace?", False),
    GoldenQuestion("n06", "What are the penalties under the Industrial Relations Code, 2020?", False),
]
