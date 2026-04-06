class countryWiseNumberPlate:
    def __init__(self, country="IN"):
        self.country = country

        self.countryNumberPlateFormats = {
            "IN": {
                "regex_list": [
                    r"^[A-Z]{2}\d{1}[A-Z]\d{4}$",         # LL D L DDDD (8)
                    r"^[A-Z]{2}\d{2}[A-Z]\d{4}$",         # LL DD L DDDD (9)
                    r"^[A-Z]{2}\d{1}[A-Z]{2}\d{4}$",      # LL D LL DDDD (9)
                    r"^[A-Z]{2}\d{2}[A-Z]{2}\d{4}$",      # LL DD LL DDDD (10)
                    r"^[A-Z]{2}[0-9][A-Z0-9][A-Z]{2}\d{4}$", # fallback
                    r"^\d{2}\s*[- ]?\sBH\s[- ]?\s*\d{4}\s*[- ]?\s*[A-HJ-NP-Z]{1,2}$"
                ],

                "uniqueFirstLetterRtoStateCode": {
                    "B": "BR", "N": "NL", "O": "OD", "S": "SK", "W": "WB"
                },
                "uniqueSecondLetterRtOStateCode": {
                    "S": "AS", "Z": "MZ", "Y": "PY"
                },

                "state_codes": [
                    "AP","AR","AS","BR","CG","CH","DD","DL","GA","GJ","HP","HR",
                    "JH","JK","KA","KL","LA","LD","MH","ML","MN","MP","MZ","NL",
                    "OD","PB","PY","RJ","SK","TN","TR","TG","TS","UK","UP","WB"
                ],

                "example": "MH12AB1234"
            }
        }
        self.combined_pattern_regex = self.combinedPattern()

    def checkRegex(self, pattern, text):
        try:
            return bool(re.match(pattern, text))
        except Exception as e:
            logger.error(f"Error in checkRegex: {e}")
            return False

    def combinedPattern(self):
        try:
            patterns = self.countryNumberPlateFormats[self.country]["regex_list"]
            combined_pattern = "|".join(f"(?:{p.strip('^$')})" for p in patterns)
            return re.compile(combined_pattern)
        except Exception as e:
            logger.error(f"Error in combinedPattern: {e}")
            return None

    def findNumberPlateFormat(self, regex, text):
        try:
            match = regex.search(text)
            if match:
                return (True, match.group())
            return (False, text)
        except Exception as e:
            logger.error(f"Error in findNumberPlateFormat: {e}")
            return (False, text)

    def checkStateCode(self, text):
        try:
            data = self.countryNumberPlateFormats[self.country]
            state_codes = data["state_codes"]
            map1 = data["uniqueFirstLetterRtoStateCode"]
            map2 = data["uniqueSecondLetterRtOStateCode"]

            if len(text) >= 2:
                state = text[:2]
                if state in state_codes:
                    return state
                if state == "OL":
                     return "DL"
                if text[0] in map1:
                    return map1[text[0]]
                if text[1] in map2:
                    return map2[text[1]]
            return text
        except Exception as e:
            logger.error(f"Error in checkStateCodes {e}")
            return text

    def correctAlphanumbericNumberPlate(self, text, check="alpha"):
        try:
            alphaMap = {'0':'O','1':'I','2':'Z','3':'E','5':'S','6':'G','7':'T','8':'B'}
            numericMap = {'O':'0','D':'0','Q':'0','I':'1','L':'1','Z':'2','S':'5','E':'3','G':'6','T':'7','Y':'7','B':'8'}
            specialMap = {'$':'S','@':'A','!':'1','|':'1'}

            corrected = ""
            for ch in text:
                if check == "alpha" and ch in alphaMap:
                    corrected += alphaMap[ch]
                elif check == "numeric" and ch in numericMap:
                    corrected += numericMap[ch]
                elif check == "special" and ch in specialMap:
                    corrected += specialMap[ch]
                else:
                    corrected += ch
            return corrected
        except Exception as e:
            logger.error(f"Error in correctAlphanumbericNumberPlate: {e}")
            return text

    def stripAndUpper(self, text):
        # Uppercase + remove non-alphanumerics
        text = text.upper()
        text = re.sub(r'[^A-Z0-9]', '', text)
        return text

    def alignToStateCode(self, text):
        """
        If the first two chars are not a state code and the string starts
        with extra letters (e.g., IND...), shift to the first valid state code.
        We do NOT convert letters to digits before finding state code.
        """
        data = self.countryNumberPlateFormats[self.country]
        state_codes = set(data["state_codes"])
        size = len(text)
        for i in range(0, max(0, size - 1)):
            if text[i:i+2] in state_codes:
                return text[i:]
        return text

    def applyGenericRules(self, text):
        # 1) uppercase + strip junk
        text = self.stripAndUpper(text)

        # 2) ignore leading IND if present
        if text.startswith("IND"):
            text = text[3:]

        # 3) convert special chars early
        text = self.correctAlphanumbericNumberPlate(text, check="special")

        # 4) align to state code if needed (before alpha->digit conversion)
        text = self.alignToStateCode(text)

        # 5) if too short to apply rules, return as-is
        if len(text) < 6:
            return text

        # 6) enforce letter/digit positions with corrections
        # positions 0-1: letters (state code), position 2: digit
        if len(text) >= 3:
            # ensure first two letters look like letters (digit->alpha)
            text = self.correctAlphanumbericNumberPlate(text[:2], check="alpha") + text[2:]
            # ensure position 2 numeric (alpha->digit)
            text = text[:2] + self.correctAlphanumbericNumberPlate(text[2], check="numeric") + text[3:]

        # last 4 digits
        if len(text) >= 4:
            last4 = self.correctAlphanumbericNumberPlate(text[-4:], check="numeric")
            text = text[:-4] + last4

        # position -5 must be letter
        if len(text) >= 5:
            p = text[-5]
            p = self.correctAlphanumbericNumberPlate(p, check="alpha")
            text = text[:-5] + p + text[-4:]

        return text

    def checkBharatNumberPate(self, text):
        try:
            allPossibilities = []
            size = len(text)
            pattern = self.countryNumberPlateFormats[self.country]["regex_list"][-1]
            compliedPattern = re.compile(pattern.strip('^$'))
            if size < 9:
                return (False, text)
            if size > 8:
                for i, ch in enumerate(text):
                    if ch == 'H' and i > 2 and (size - 4) >= 5:
                        candidate = text[:i-1] + 'B' + text[i:]
                        try:
                            yearTxt = self.correctAlphanumbericNumberPlate(candidate[i-3:i-1], check="numeric")
                            NumText = self.correctAlphanumbericNumberPlate(candidate[i+1:i+5], check="numeric")
                            alphaTxt = self.correctAlphanumbericNumberPlate(candidate[i+5:i+7], check="alpha")
                            candidate = candidate[:i-3] + yearTxt + candidate[i-1:i+1] + NumText + alphaTxt + candidate[i+7:]
                            allPossibilities.append(candidate)
                        except Exception:
                            continue

                for tentativeText in allPossibilities:
                    found, checkText = self.findNumberPlateFormat(compliedPattern, tentativeText)
                    if found:
                        return (True, checkText)
            return (False, text)
        except Exception as e:
            logger.error(f"Error in checkBharatNumberPate: {e}")
            return (False, text)

    def getNumberPlateFormat(self, text):
        try:
            def formatPlate(t):
                st = t[:2]
                newState = self.checkStateCode(st)
                last4 = self.correctAlphanumbericNumberPlate(t[-4:], check="numeric")
                return f"{newState}{t[2:-4]}{last4}"

            def checkNumberPlateCorrectness(text, size):
                try:
                    data = self.countryNumberPlateFormats[self.country]
                    state_codes = data["state_codes"]
                    state = text[:2]
                    if state not in state_codes:
                        return 0
                    if not text[-4:].isdigit():
                        return 0
                    if size == 8:
                        # LLDLDDDD
                        if not (text[2].isdigit() and text[3].isalpha()):
                            return 0
                    if size == 9:
                        # LLD(DL or LL)DDDD
                        if not ((text[2].isdigit() and text[3].isdigit() and text[4].isalpha()) or
                                (text[2].isdigit() and text[3].isalpha() and text[4].isalpha())):
                            return 0
                    if size == 10:
                        # LLDDLLDDDD (DL exception: index 3 can be letter)
                        if state == "DL":
                            if not (text[2].isdigit() and (text[3].isdigit() or text[3].isalpha())):
                                return 0
                        else:
                            if not (text[2].isdigit() and text[3].isdigit()):
                                return 0
                        if not (text[4:6].isalpha()):
                            return 0
                    return 1
                except Exception as e:
                    logger.error(f"Error in checkNumberPlateCorrectness: {e}")
                    return 0

            patterns = self.countryNumberPlateFormats[self.country]["regex_list"]
            if not text:
                return (text, 0)

            # apply generic normalization + rules
            text = self.applyGenericRules(text)
            size = len(text)

            if size == 8:
                if self.checkRegex(patterns[0], text):
                    finalPlate = formatPlate(text)
                    check = checkNumberPlateCorrectness(finalPlate, size)
                    return (finalPlate, check)

            if size == 9:
                if self.checkRegex(patterns[1], text) or self.checkRegex(patterns[2], text):
                    finalPlate = formatPlate(text)
                    check = checkNumberPlateCorrectness(finalPlate, size)
                    return (finalPlate, check)

            if size == 10:
                if self.checkRegex(patterns[3], text) or self.checkRegex(patterns[4], text):
                    finalPlate = formatPlate(text)
                    check = checkNumberPlateCorrectness(finalPlate, size)
                    return (finalPlate, check)

            # only Bharat fallback now (no substring matching)
            if size > 8:
                bharatCheck, bharatText = self.checkBharatNumberPate(text)
                if bharatCheck:
                    return (bharatText, 1)

            return (text, 0)

        except Exception as e:
            logger.error(f"Error in getNumberPlateFormat: {e}")
            return (text, 0)
