
def create_peptide_regex(query):
    # Split strings into letter position pairs
    pairs = list(map(lambda p: p.strip(), query.split(",")))

    # Define function for validating pairs
    validate_pair = lambda p: len(p) == 2 and p[0].isalpha() and p[1].isdigit() and int(p[1]) > 0

    # filter out invalid pairs
    pairs = list(filter(validate_pair, pairs))

    # Return a regex that matches nothing if there are no pairs
    if not pairs:
        return "$^"

    # transform pairs to tuples
    pairs = list(map(lambda p: [p[0].upper(), int(p[1])], pairs))
    
    # Now remove remove duplicate pairs and duplicate positions
    final_pairs = []
    seen_postions = set()
    for pair in pairs:
        if pair[1] in seen_postions:
            continue
        final_pairs.append(pair)
        seen_postions.add(pair[1])

    # Now convert pairs into regex
    sort_function = lambda p: p[1]
    final_pairs.sort(key=sort_function)

    for i in reversed(range(1, len(final_pairs))):
        prev_index = final_pairs[i-1][1]
        curr_pair = final_pairs[i]
        final_pairs[i] = [curr_pair[0], curr_pair[1]-prev_index]

    for i in range(len(final_pairs)):
        final_pairs[i][1] -= 1

    regex_sections = list(map(lambda p: "{{{index}}}[{let}]".format(index=p[1], let=p[0]), final_pairs))
    final_regex = "^." + ".".join(regex_sections) + ".*"

    return final_regex


def add_bold_tags_to_peptides(query, peptide):
    peptide_letters = list(peptide)
    
    # Insert bold tags between letters
    for i in range(len(peptide_letters)):
        if peptide_letters[i] + str(i+1) in query:
            peptide_letters[i] = "<b>" + peptide_letters[i] + "</b>"

    return "".join(peptide_letters)

