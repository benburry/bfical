from BFIParser.BFIParser import parse_event_page, parse_listings_page, generate_listing_urls

__author__ = 'ben'

TEST_EVENT_URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/film_programme/november_seasons/rediscovering_frank_capra/it_happened_one_night'
#TEST_EVENT_URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/film_programme/regular_strands/studio_screenings/police_adjective'
#TEST_EVENT_URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/events/african_odysseys/new_nigeria_cinema_the_figurine'
#TEST_EVENT_URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/events/london'
#TEST_EVENT_URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/film_programme/november_seasons/rediscovering_frank_capra/submarine'
#TEST_EVENT_URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/events/a_day_in_the_life_four_portraits_of_postwar_britain'
#TEST_EVENT_URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/events/african_odysseys/african_odysseys_the_negro_soldier_discussion'
TEST_EVENT_URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/events/projecting_the_archive_/_capital_tales/projecting_the_archive_i_was_happy_here'
#TEST_EVENT_URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/film_programme/regular_strands/previews_in_conversation/preview_another_year_mike_leig'
#TEST_EVENT_URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/events/missing_believed_wiped_session_1_music_miscellany'
#TEST_EVENT_URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/events/african_odysseys_cy_grant_tribute'
TEST_EVENT_URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/film_programme/november_seasons/clandest%C3%AD_invisible_catalan_cinema_under_franco/countr'
TEST_EVENT_URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/film_programme/november_seasons/rediscovering_frank_capra/the_way_of_the_strong'
TEST_EVENT_URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/film_programme/regular_strands/studio_screenings/metropolis'
#TEST_EVENT_URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/events/misfits_character_workshop'

TEST_LISTING_URL = 'http://www.bfi.org.uk/whatson/calendar/southbank/day/20110112'
#TEST_LISTING_URL = 'http://www.bfi.org.uk/whatson/calendar/imax/day/20101116'

if __name__ == '__main__':
    (year, urls) = parse_listings_page(TEST_LISTING_URL)
#    urls = generate_listing_urls()
    for url in urls:
        print unicode(url), year
        event = parse_event_page(unicode(url), year)
        print unicode(event)
        for showing in event.showings:
            print unicode(showing)
#    event = parse_event_page(TEST_EVENT_URL)
#    print unicode(event)
#    for showing in event.showings:
#        print unicode(showing)

