import xml.etree.ElementTree as elem_tree

from itertools import zip_longest


def make_list_of_xml_tags(tag_name='', elem_name=''):

    tags = []
    for tag in elem_name.iter(tag_name):
        tags.append(tag)
    return tags


def make_dict_of_xml(elem='', elements=[]):

    keys = []
    [keys.append(element.attrib[elem]) for element in elements if
     element.attrib[elem] not in keys]
    elements_dict = dict.fromkeys(keys)

    return elements_dict


def parse_xml(file_name):

    flights_xml = elem_tree.parse(file_name)
    flights_root = flights_xml.getroot()
    routes_tree = flights_root[1]
    routes_info = []
    for route in routes_tree:
        routes_info.append(route)

    return routes_info


def all_flights(elem):
    flights_available = make_list_of_xml_tags('Flight', elem)
    flight_info = make_list_of_xml_tags('*', flights_available[0])
    flight_info.pop(0)
    flight_info_tags = []
    for flight in flight_info:
        flight_info_tags.append(flight.tag)
    flight_info_tags = dict.fromkeys(flight_info_tags)

    flights = []
    for available in flights_available:
        flight_specs = {**flight_info_tags}
        specs_for_flight = available.findall('*')
        for spec in specs_for_flight:
            flight_specs[spec.tag] = spec.text
        flights.append(flight_specs)

    return flights


def pricing(elem):
    services = make_list_of_xml_tags('ServiceCharges', elem)

    service_types = make_dict_of_xml('type', services)
    charge_types = make_dict_of_xml('ChargeType', services)

    for typo in service_types:
        service_types[typo] = {**charge_types}

    attribs = []
    for service in services:
        base_attribs = service.attrib
        base_attribs['price'] = service.text
        attribs.append(base_attribs)

    for attrib in attribs:
        for serv in service_types.keys():
            if attrib['type'] == serv:
                for charge in charge_types.keys():
                    if attrib['ChargeType'] == charge:
                        price = attrib['price']
                        service_types[attrib['type']][attrib['ChargeType']] = price

    return service_types


def routes_from_request(request):

    routes = []

    for flight in request:
        route_info = flight.findall('*')
        route_template = {
            'Onward_priced': None,
            'Return_priced': None,
            'Route_pricing': None,
        }
        info_template = {**route_template}

        for info in route_info:

            if info.tag == "Pricing":
                pricings = pricing(info)
                info_template['Route_pricing'] = pricings

            elif info.tag == 'OnwardPricedItinerary':
                onwards = all_flights(info)
                info_template['Onward_priced'] = onwards

            elif info.tag == 'ReturnPricedItinerary':
                returns = all_flights(info)
                info_template['Return_priced'] = returns

        routes.append(info_template)

    return routes


def show_flight_info(flight):
    print('Flight info:')
    for flight_info in flight.items():
        if flight_info[0] != 'FareBasis':
            print(f'{flight_info[0]} : {flight_info[1]}')
    print('\n')


def flight_comparison(first_route, second_route):
    if first_route and second_route:
        for two_flights in zip_longest(first_route, second_route):
            if not two_flights[0]:
                print('New flight available:\n')
                show_flight_info(two_flights[1])
            elif not two_flights[1]:
                print('This flight is no longer available:\n')
                show_flight_info(two_flights[0])
            elif two_flights[0]['FlightNumber'] != two_flights[1]['FlightNumber']:
                print(f"Flight number: {two_flights[0]['FlightNumber']} is not available.")
                print('Substituted with:\n')
                show_flight_info(two_flights[1])

            else:
                flight_changes = []
                for compare in zip(two_flights[0].items(), two_flights[1].items()):
                    if compare[0] != compare[1] and compare[0][0] != 'FareBasis':
                        flight_changes.append(compare[1])

                if flight_changes:
                    print(f"Flight number {two_flights[0]['FlightNumber']} has been updated:")
                    for change in flight_changes:
                        print(f"New {change[0]} : {change[1]}")
                    print('\n')
                else:
                    print('No changes for flights in this route.\n')

    elif not second_route:
        print('These flights are no longer available:\n')
        for flight in first_route:
            show_flight_info(flight)

    elif not first_route:
        print('New flights are available:\n')
        for flight in second_route:
            show_flight_info(flight)


if __name__ == '__main__':

    first_request = parse_xml('RS_Via-3.xml')
    second_request = parse_xml('RS_ViaOW.xml')

    routes_in_first = routes_from_request(first_request)
    routes_in_second = routes_from_request(second_request)

    for route_1, route_2 in zip_longest(routes_in_first, routes_in_second):
        if route_1 and route_2:
            print('REQUESTED ROUTE COMPARISON:')
            print('ONWARD PRICED ITINERARY:\n')
            flight_comparison(
                route_1['Onward_priced'],
                route_2['Onward_priced']
                )
            print('RETURN PRICED ITINERARY:\n')
            flight_comparison(
                route_1['Return_priced'],
                route_2['Return_priced']
                )
            print('ROUTE PRICING:\n')
            route_1_prices, route_2_prices = route_1['Route_pricing'], route_2['Route_pricing']
            if route_1_prices != route_2_prices:
                print('Prices updated:')
                print(route_2_prices)

        elif not route_2:
            print('REQUESTED ROUTE COMPARISON:\nThis route is no longer available!\n')
            print('ONWARD PRICED ITINERARY:\nThese flights are no longer available:\n')
            for flight in route_1['Onward_priced']:
                show_flight_info(flight)
            print('RETURN PRICED ITINERARY:\nThese flights are no longer available:\n')
            for flight in route_1['Return_priced']:
                show_flight_info(flight)

            print('ROUTE PRICING:\nCharges for this route were:\n')
            print(route_1['Route_pricing'])
