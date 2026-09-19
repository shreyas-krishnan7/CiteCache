"""
Golden set for the Indian labour-law corpus in data/docs_labour/:
the Occupational Safety, Health and Working Conditions Code, 2020;
the Code on Wages, 2019; and the Bonded Labour System (Abolition)
Act, 1976.

reference_answer rules. Each exists because RAGAS mis-scored correct answers
without it -- see the audit traces behind each:
  1. Attribute to the Act AND the section ("Under section 8(4) of the Code on
     Wages, 2019, ..."). FactualCorrectness matches each claim's attribution
     in both directions: a reference citing only "Section 8(4)" scored a
     correct answer citing "the Code on Wages 2019" at 0.00.
  2. Each sentence rests on a single provision. LLMContextRecall judges whole
     sentences, so one sentence mixing a retrieved fact with an unretrieved
     one scores zero even when the retrieved fact is right there.
  3. Answer only what the question asks. Facts the question does not ask for
     penalise a correct, focused answer and may not be in the retrieved context.
  4. Every fact is checked against the statute text; nothing is paraphrased
     into a different number or name.

expected_source values are the ingested file stems, so they only match
if data/docs_labour was ingested with those filenames.
"""
from __future__ import annotations

from app.eval.golden_set import GoldenQuestion

OSH = "osh_code_2020"
WAGES = "code_on_wages_2019"
BONDED = "bonded_labour_act_1976"

_BLA = "the Bonded Labour System (Abolition) Act, 1976"
_COW = "the Code on Wages, 2019"
_OSH = "the Occupational Safety, Health and Working Conditions Code, 2020 (OSH Code)"


GOLDEN_SET: list[GoldenQuestion] = [
    # ---------- Bonded Labour System (Abolition) Act, 1976 ----------
    GoldenQuestion("b01", "What is the punishment for compelling a person to render bonded labour?",
                   True, BONDED, ["three years", "two thousand"],
                   f"Under section 16 of {_BLA}, whoever compels any person to render bonded labour is "
                   f"punishable with imprisonment for a term which may extend to three years. The offender is "
                   f"also punishable with a fine which may extend to two thousand rupees."),
    GoldenQuestion("b02", "Who bears the burden of proof when a debt is claimed to be a bonded debt?",
                   True, BONDED, ["creditor", "burden"],
                   f"Under section 15 of {_BLA}, the burden of proof lies on the creditor. Whenever a bonded "
                   f"labourer or a Vigilance Committee claims a debt to be a bonded debt, the creditor must prove "
                   f"that the debt is not a bonded debt."),
    GoldenQuestion("b03", "What happened to bonded debts when the Act came into force?",
                   True, BONDED, ["extinguished"],
                   f"Under section 6 of {_BLA}, every obligation of a bonded labourer to repay a bonded debt was "
                   f"deemed to have been extinguished on the commencement of the Act. No suit or other proceeding "
                   f"lies in any civil court or before any other authority for the recovery of a bonded debt. "
                   f"Every decree or order for the recovery of a bonded debt not fully satisfied before the "
                   f"commencement was deemed to have been fully satisfied. Every suit or proceeding for the "
                   f"recovery of a bonded debt pending at the commencement stood dismissed."),
    GoldenQuestion("b04", "Can a freed bonded labourer be evicted from their homestead?",
                   True, BONDED, ["evicted", "executive magistrate"],
                   f"No. Under section 8 of {_BLA}, a freed bonded labourer shall not be evicted from any "
                   f"homestead or other residential premises occupied as part of the consideration for the bonded "
                   f"labour. If the creditor evicts such a person, the Executive Magistrate in charge of the "
                   f"Sub-Division must restore the person to possession as early as practicable."),
    GoldenQuestion("b05", "Who chairs a district Vigilance Committee and how many members must belong "
                          "to the Scheduled Castes or Scheduled Tribes?",
                   True, BONDED, ["district magistrate", "three"],
                   f"Under section 13(2) of {_BLA}, the District Magistrate, or a person nominated by the District "
                   f"Magistrate, is the Chairman of a district Vigilance Committee. The committee includes three "
                   f"persons belonging to the Scheduled Castes or Scheduled Tribes who reside in the district, "
                   f"nominated by the District Magistrate."),
    GoldenQuestion("b06", "What is the penalty if a creditor accepts payment against a debt that has "
                          "already been extinguished?",
                   True, BONDED, ["three years"],
                   f"Under section 9 of {_BLA}, a creditor who accepts payment against an extinguished bonded debt "
                   f"is punishable with imprisonment for a term which may extend to three years and also with fine. "
                   f"The convicting court may also direct the creditor to deposit the amount accepted in court, for "
                   f"refund to the bonded labourer."),
    GoldenQuestion("b07", "When is the Bonded Labour System (Abolition) Act deemed to have come into force?",
                   True, BONDED, ["25th day of october, 1975"],
                   f"Under section 1(3) of {_BLA}, the Act is deemed to have come into force on the 25th day of "
                   f"October, 1975."),
    GoldenQuestion("b08", "What is the punishment for abetting an offence under the Bonded Labour "
                          "System (Abolition) Act?",
                   True, BONDED, ["same punishment"],
                   f"Under section 20 of {_BLA}, whoever abets an offence punishable under the Act is punishable "
                   f"with the same punishment as is provided for the offence abetted. This applies whether or not "
                   f"the abetted offence is committed."),

    # ---------- Code on Wages, 2019 ----------
    GoldenQuestion("w01", "What is the overtime rate under the Code on Wages?",
                   True, WAGES, ["twice"],
                   f"Under section 14 of {_COW}, an employee who works in excess of the hours constituting a normal "
                   f"working day must be paid for every hour or part of an hour worked in excess at the overtime "
                   f"rate. The overtime rate shall not be less than twice the normal rate of wages."),
    GoldenQuestion("w02", "By when must an employer pay wages to a monthly-paid employee?",
                   True, WAGES, ["seventh day"],
                   f"Under section 17(1) of {_COW}, wages of an employee engaged on a monthly basis must be paid "
                   f"before the expiry of the seventh day of the succeeding month."),
    GoldenQuestion("w03", "When must wages be paid to an employee who has been dismissed or has resigned?",
                   True, WAGES, ["two working days"],
                   f"Under section 17(2) of {_COW}, the wages payable to an employee who has been removed, dismissed "
                   f"or retrenched, or who has resigned, must be paid within two working days of the removal, "
                   f"dismissal, retrenchment or resignation."),
    GoldenQuestion("w04", "What is the maximum total deduction that can be made from an employee's "
                          "wages in a wage period?",
                   True, WAGES, ["fifty per cent"],
                   f"Under section 18(3) of {_COW}, the total amount of deductions from an employee's wages in any "
                   f"wage period shall not exceed fifty per cent of such wages."),
    GoldenQuestion("w05", "What limits apply to fines imposed on an employee, and can a 14-year-old "
                          "be fined?",
                   True, WAGES, ["three per cent", "fifteen years"],
                   f"Under section 19(4) of {_COW}, the total fine imposed on an employee in any one wage period "
                   f"shall not exceed three per cent of the wages payable for that wage period. Under section 19(5) "
                   f"of {_COW}, no fine shall be imposed on an employee who is under the age of fifteen years, so a "
                   f"14-year-old employee cannot be fined."),
    GoldenQuestion("w06", "What is the minimum bonus payable under the Code on Wages?",
                   True, WAGES, ["eight and one-third per cent", "one hundred rupees", "thirty days"],
                   f"Under section 26(1) of {_COW}, an employee who has put in at least thirty days of work in an "
                   f"accounting year is entitled to an annual minimum bonus. The minimum bonus is eight and "
                   f"one-third per cent of the wages earned by the employee or one hundred rupees, whichever is "
                   f"higher. It is payable whether or not the employer has any allocable surplus."),
    GoldenQuestion("w07", "Within what time must bonus be paid?",
                   True, WAGES, ["eight months"],
                   f"Under section 39(1) of {_COW}, bonus must be paid by crediting it to the employee's bank "
                   f"account within eight months from the close of the accounting year. The appropriate Government "
                   f"may extend this period on the employer's application for sufficient reasons, but the total "
                   f"extended period shall not exceed two years."),
    GoldenQuestion("w08", "What disqualifies an employee from receiving bonus?",
                   True, WAGES, ["fraud", "sexual harassment"],
                   f"Under section 29 of {_COW}, an employee is disqualified from receiving bonus if dismissed from "
                   f"service for fraud; for riotous or violent behaviour while on the premises of the establishment; "
                   f"for theft, misappropriation or sabotage of any property of the establishment; or for conviction "
                   f"for sexual harassment."),
    GoldenQuestion("w09", "What is the time limit for filing a claim under the Code on Wages?",
                   True, WAGES, ["three years"],
                   f"Under section 45(6) of {_COW}, an application for a claim may be filed within three years from "
                   f"the date on which the claim arises. The authority may entertain an application after three "
                   f"years if the applicant shows sufficient cause for the delay."),
    GoldenQuestion("w10", "What is the penalty for an employer who pays an employee less than the "
                          "amount due, and what happens on a repeat offence?",
                   True, WAGES, ["fifty thousand", "one lakh", "three months"],
                   f"Under section 54(1)(a) of {_COW}, an employer who pays an employee less than the amount due is "
                   f"punishable with a fine which may extend to fifty thousand rupees. Under section 54(1)(b) of "
                   f"{_COW}, an employer convicted of that offence who is again found guilty of a similar offence "
                   f"within five years is punishable with imprisonment which may extend to three months, or with a "
                   f"fine which may extend to one lakh rupees, or with both."),
    GoldenQuestion("w11", "How often must minimum wages be reviewed or revised?",
                   True, WAGES, ["five years"],
                   f"Under section 8(4) of {_COW}, the appropriate Government must review or revise minimum rates of "
                   f"wages ordinarily at an interval not exceeding five years."),
    GoldenQuestion("w12", "Is house rent allowance included in 'wages' under the Code on Wages?",
                   True, WAGES, ["house rent allowance", "one-half"],
                   f"Under section 2(y) of {_COW}, wages include basic pay, dearness allowance and retaining "
                   f"allowance, and exclude house rent allowance. However, if the excluded payments exceed one-half "
                   f"of the total remuneration, or such other percentage as the Central Government notifies, the "
                   f"excess is deemed to be remuneration and is added to wages. For the purposes of equal wages for "
                   f"all genders and of payment of wages, house rent allowance is taken into account in computing "
                   f"wages."),
    GoldenQuestion("w13", "Can an offence under the Code on Wages be compounded, and at what cost?",
                   True, WAGES, ["fifty per cent"],
                   f"Under section 56(1) of {_COW}, an offence that is not punishable with imprisonment only, or with "
                   f"imprisonment and also with fine, may be compounded by a notified Gazetted Officer for a sum of "
                   f"fifty per cent of the maximum fine provided for the offence. Under section 56(2) of {_COW}, this "
                   f"does not apply to a similar offence committed a second time within five years of an earlier "
                   f"compounded offence or conviction."),
    GoldenQuestion("w14", "Who is excluded from the definition of 'worker' under the Code on Wages?",
                   True, WAGES, ["apprentice", "fifteen thousand"],
                   f"Under section 2(z) of {_COW}, an apprentice as defined under the Apprentices Act, 1961 is "
                   f"excluded from the definition of worker. A person subject to the Air Force Act, 1950, the Army "
                   f"Act, 1950 or the Navy Act, 1957 is excluded. A person employed in the police service, or as an "
                   f"officer or other employee of a prison, is excluded. A person employed mainly in a managerial or "
                   f"administrative capacity is excluded. A person employed in a supervisory capacity drawing wages "
                   f"exceeding fifteen thousand rupees per month, or such amount as the Central Government notifies, "
                   f"is excluded."),

    # ---------- Occupational Safety, Health and Working Conditions Code, 2020 ----------
    GoldenQuestion("o01", "How many hours a day and days a week can a worker be required to work "
                          "under the OSH Code?",
                   True, OSH, ["eight hours", "six days"],
                   f"Under section 25(1) of {_OSH}, no worker shall be required or allowed to work in an "
                   f"establishment for more than eight hours in a day. Under section 26(1) of the OSH Code, no "
                   f"worker shall be allowed to work in an establishment for more than six days in any one week."),
    GoldenQuestion("o02", "What overtime rate applies under the OSH Code and is the worker's consent "
                          "required?",
                   True, OSH, ["twice", "consent"],
                   f"Under section 27 of {_OSH}, wages for overtime work are paid at twice the rate of wages where "
                   f"a worker works for more than the hours prescribed by the appropriate Government in a day or a "
                   f"week. The period of overtime work is calculated on a daily or weekly basis, whichever is more "
                   f"favourable to the worker. A worker may be required to work overtime only with the worker's "
                   f"consent."),
    GoldenQuestion("o03", "How much annual leave with wages is a worker entitled to under the OSH Code?",
                   True, OSH, ["one hundred and eighty days", "twenty days", "fifteen days"],
                   f"Under section 32(1) of {_OSH}, a worker is entitled to leave with wages if the worker has "
                   f"worked for one hundred and eighty days or more in a calendar year. The worker earns one day of "
                   f"leave for every twenty days of work. An adolescent worker earns one day of leave for every "
                   f"fifteen days of work. A worker employed below ground in a mine earns one day of leave for "
                   f"every fifteen days of work."),
    GoldenQuestion("o04", "When must an employer appoint a safety officer?",
                   True, OSH, ["five hundred", "two hundred fifty", "one hundred"],
                   f"Under section 22(2) of {_OSH}, the employer must appoint safety officers in a factory in which "
                   f"five hundred or more workers are ordinarily employed. Safety officers are also required in a "
                   f"factory carrying on a hazardous process in which two hundred fifty or more workers are "
                   f"ordinarily employed. They are required in building or other construction work in which two "
                   f"hundred fifty or more workers are ordinarily employed. They are required in a mine in which "
                   f"one hundred or more workers are ordinarily employed."),
    GoldenQuestion("o05", "When is a canteen required, and when is a creche required?",
                   True, OSH, ["one hundred", "fifty"],
                   f"Under section 24(1) of {_OSH}, canteen facilities must be provided in an establishment in "
                   f"which one hundred or more workers, including contract labourers, are ordinarily employed. "
                   f"Under section 24(3) of the OSH Code, the Central Government may make rules providing a creche "
                   f"for employees' children under the age of six years in establishments in which more than fifty "
                   f"workers are ordinarily employed."),
    GoldenQuestion("o06", "Can women be employed at night under the OSH Code?",
                   True, OSH, ["consent", "6 a.m.", "7 p.m."],
                   f"Yes. Under section 43 of {_OSH}, women are entitled to be employed in all establishments for "
                   f"all types of work. With their consent, women may be employed before 6 a.m. and beyond 7 p.m., "
                   f"subject to conditions relating to safety, holidays and working hours prescribed by the "
                   f"appropriate Government."),
    GoldenQuestion("o07", "Within how many days must a new establishment apply for registration?",
                   True, OSH, ["sixty days"],
                   f"Under section 3(1) of {_OSH}, the employer of a new establishment to which the Code applies "
                   f"must apply electronically to the registering officer for registration within sixty days from "
                   f"the date on which the Code becomes applicable to it. The registering officer may entertain an "
                   f"application made after that period on payment of the late fee prescribed by the appropriate "
                   f"Government."),
    GoldenQuestion("o08", "When do the contract labour provisions of the OSH Code apply?",
                   True, OSH, ["fifty or more"],
                   f"Under section 45(1) of {_OSH}, the contract labour provisions apply to every establishment in "
                   f"which fifty or more contract labour are employed, or were employed on any day of the preceding "
                   f"twelve months. They also apply to every manpower supply contractor who has employed fifty or "
                   f"more contract labour on any day of the preceding twelve months. Under section 45(2) of the OSH "
                   f"Code, they do not apply to an establishment in which only work of an intermittent or casual "
                   f"nature is performed."),
    GoldenQuestion("o09", "What happens if a contractor fails to pay wages to contract labour?",
                   True, OSH, ["principal employer", "recover"],
                   f"Under section 55(3) of {_OSH}, if a contractor fails to pay wages to contract labour within the "
                   f"prescribed period or makes a short payment, the principal employer is liable to pay the wages "
                   f"in full or the unpaid balance. The principal employer may recover the amount paid from the "
                   f"contractor, either by deduction from any amount payable to the contractor or as a debt payable "
                   f"by the contractor."),
    GoldenQuestion("o10", "When do the inter-State migrant worker provisions apply, and what travel "
                          "benefit do such workers receive?",
                   True, OSH, ["ten or more", "journey"],
                   f"Under section 59 of {_OSH}, the provisions on inter-State migrant workers apply to every "
                   f"establishment in which ten or more inter-State migrant workers are employed, or were employed "
                   f"on any day of the preceding twelve months. Under section 61 of the OSH Code, the employer must "
                   f"pay every inter-State migrant worker, in a year, a lump sum amount of fare for a to and fro "
                   f"journey to the worker's native place from the place of employment."),
    GoldenQuestion("o11", "Which accidents must be notified under the OSH Code?",
                   True, OSH, ["forty-eight hours", "death"],
                   f"Under section 10(1) of {_OSH}, notice must be sent of an accident in an establishment that "
                   f"causes death. Notice must also be sent of an accident that causes bodily injury preventing the "
                   f"injured person from working for a period of forty-eight hours or more immediately following "
                   f"the accident. Notice is also required for an accident of such other nature as the appropriate "
                   f"Government prescribes."),
    GoldenQuestion("o12", "What is the general penalty for contravening the OSH Code?",
                   True, OSH, ["two lakh", "three lakh", "two thousand"],
                   f"Under section 94 of {_OSH}, for a contravention of the Code the employer or principal employer "
                   f"is liable to a penalty of not less than two lakh rupees, which may extend to three lakh rupees. "
                   f"If the contravention continues after conviction, a further penalty which may extend to two "
                   f"thousand rupees applies for each day the contravention continues."),
    GoldenQuestion("o13", "What is the punishment when a safety contravention results in a worker's death?",
                   True, OSH, ["two years", "five lakh", "fifty per cent"],
                   f"Under section 103(1)(a) of {_OSH}, where a contravention of duties results in an accident or "
                   f"dangerous occurrence causing death, the person is punishable with imprisonment which may extend "
                   f"to two years, or with a fine of not less than five lakh rupees, or with both. The court may "
                   f"direct that not less than fifty per cent of the fine be given as compensation to the legal "
                   f"heirs of the victim."),
    GoldenQuestion("o14", "What counts as a 'factory' and what counts as an 'establishment' under the "
                          "OSH Code?",
                   True, OSH, ["twenty or more", "forty or more", "ten or more"],
                   f"Under section 2(1)(w) of {_OSH}, a factory is any premises on which twenty or more workers are "
                   f"working, or were working on any day of the preceding twelve months, and in any part of which a "
                   f"manufacturing process is carried on with the aid of power. Premises on which forty or more "
                   f"workers are working, or were working on any day of the preceding twelve months, and in any part "
                   f"of which a manufacturing process is carried on without the aid of power are also a factory. "
                   f"Under section 2(1)(v) of the OSH Code, an establishment is a place where any industry, trade, "
                   f"business, manufacturing or occupation is carried on in which ten or more workers are employed. "
                   f"That threshold does not apply to an establishment carrying on a hazardous or life-threatening "
                   f"activity notified by the Central Government."),
    GoldenQuestion("o15", "What rights does an employee have when there is imminent danger at the "
                          "workplace?",
                   True, OSH, ["imminent", "inspector-cum-facilitator"],
                   f"Under section 14(2) of {_OSH}, an employee who has a reasonable apprehension of a likelihood of "
                   f"imminent serious personal injury or death, or imminent danger to health, may bring it to the "
                   f"notice of the employer, directly or through a member of the Safety Committee, and "
                   f"simultaneously to the notice of the Inspector-cum-Facilitator. Under section 14(3) of the OSH "
                   f"Code, the employer must take immediate remedial action if satisfied that such imminent danger "
                   f"exists. Under section 14(4) of the OSH Code, if the employer is not satisfied that the imminent "
                   f"danger exists, the employer must still refer the matter to the Inspector-cum-Facilitator, whose "
                   f"decision on the question is final."),
    GoldenQuestion("o16", "Is employment of contract labour allowed in an establishment's core activity?",
                   True, OSH, ["core activit", "prohibited"],
                   f"Under section 57(1) of {_OSH}, employment of contract labour in the core activities of any "
                   f"establishment is prohibited. The principal employer may nevertheless engage contract labour in "
                   f"a core activity if the normal functioning of the establishment is such that the activity is "
                   f"ordinarily done through a contractor. It is also allowed if the activity does not require "
                   f"full-time workers for the major portion of the working hours in a day or for longer periods. It "
                   f"is also allowed for a sudden increase in the volume of work in the core activity that needs to "
                   f"be accomplished in a specified time."),

    # ---------- Cross-document (multi-hop retrieval) ----------
    GoldenQuestion("x01", "How does the Bonded Labour Act define 'nominal wages', and how does that "
                          "relate to minimum wages legislation?",
                   True, None, ["minimum wage", "locality"],
                   f"Under section 2(i) of {_BLA}, nominal wages means a wage less than the minimum wages fixed by "
                   f"the Government for the same or similar labour under any law for the time being in force. Where "
                   f"no minimum wage has been fixed for a form of labour, nominal wages means a wage less than the "
                   f"wages normally paid for the same or similar labour to labourers working in the same locality. "
                   f"Under section 5 of {_COW}, no employer shall pay an employee wages less than the minimum rate "
                   f"of wages notified by the appropriate Government. Under section 9 of {_COW}, the minimum rates of "
                   f"wages fixed by the appropriate Government shall not be less than the floor wage fixed by the "
                   f"Central Government."),
    GoldenQuestion("x02", "Does the definition of 'contract labour' differ between the Code on Wages "
                          "and the OSH Code?",
                   True, None, ["contractor", "principal employer"],
                   f"No, the two definitions are substantively the same. Under section 2(g) of {_COW}, contract "
                   f"labour means a worker deemed to be employed in or in connection with the work of an "
                   f"establishment when hired in or in connection with such work by or through a contractor, with "
                   f"or without the knowledge of the principal employer. Under section 2(1)(m) of {_OSH}, contract "
                   f"labour is defined in the same terms. Both definitions include inter-State migrant workers. Both "
                   f"definitions exclude a worker, other than a part-time employee, who is regularly employed by the "
                   f"contractor under mutually accepted standards of the conditions of employment and who gets "
                   f"periodical increments in pay, social security coverage and other welfare benefits."),
    GoldenQuestion("x03", "Both the Code on Wages and the OSH Code provide for overtime. Do they set "
                          "the same rate?",
                   True, None, ["twice"],
                   f"Yes, both set overtime at twice the normal rate of wages. Under section 14 of {_COW}, overtime "
                   f"must be paid at a rate not less than twice the normal rate of wages for every hour or part of an "
                   f"hour worked in excess of a normal working day. Under section 27 of {_OSH}, wages for overtime "
                   f"work are paid at twice the rate of wages. Under section 27 of the OSH Code, the period of "
                   f"overtime work is calculated on a daily or weekly basis, whichever is more favourable to the "
                   f"worker."),
    GoldenQuestion("x04", "Does the Bonded Labour System (Abolition) Act cover contract labour and "
                          "inter-State migrant workers?",
                   True, BONDED, ["contract labour", "inter-state migrant"],
                   f"Yes. Under the Explanation to section 2(g) of {_BLA}, added by the Bonded Labour System "
                   f"(Abolition) Amendment Act, 1985, forced or partly forced labour required of contract labour as "
                   f"defined in the Contract Labour (Regulation and Abolition) Act, 1970 is within the bonded labour "
                   f"system. The same Explanation covers an inter-State migrant workman as defined in the Inter-State "
                   f"Migrant Workmen (Regulation of Employment and Conditions of Service) Act, 1979."),
    GoldenQuestion("x05", "Both Codes make company officers liable for offences. What must be proved "
                          "against a director?",
                   True, None, ["consent", "connivance", "neglect"],
                   f"Under section 55(2) of {_COW}, where an offence is committed by a company, a director, manager, "
                   f"secretary or other officer is also guilty if it is proved that the offence was committed with "
                   f"that officer's consent or connivance, or is attributable to any neglect on that officer's part. "
                   f"Under section 109(2) of {_OSH}, the same must be proved against a director, manager, company "
                   f"secretary or other officer: consent or connivance, or neglect to which the offence is "
                   f"attributable."),

    # ---------- Out-of-corpus: correct behaviour is insufficient_context=True ----------
    # Each is adjacent to the corpus but its answer lives in a statute that is not ingested.
    GoldenQuestion("n01", "What is the current national floor wage in rupees per day?", False),
    GoldenQuestion("n02", "How many weeks of paid maternity leave is a woman worker entitled to?", False),
    GoldenQuestion("n03", "What is the employer's contribution rate to the Employees' Provident Fund?", False),
    GoldenQuestion("n04", "How is gratuity calculated on termination of employment?", False),
    GoldenQuestion("n05", "What is the procedure for filing a sexual harassment complaint at the workplace?", False),
    GoldenQuestion("n06", "What are the penalties under the Industrial Relations Code, 2020?", False),
]
