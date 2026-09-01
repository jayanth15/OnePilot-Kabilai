def _format_price(price: float) -> str:
    if price == int(price):
        return f"\u20b9{int(price)}"
    return f"\u20b9{price}"


def greeting_msg(brand: str) -> str:
    return (
        f"Namaste! Welcome to *{brand}* \U0001f37f\n\n"
        f"I can help you with:\n"
        f"1. View our dairy products\n"
        f"2. Check price of a product\n"
        f"3. Check delivery to your area\n"
        f"4. Place an enquiry\n"
        f"5. Talk to our team\n\n"
        f"Please reply with a number or ask your question."
    )


def products_list_msg(brand: str, products: list) -> str:
    if not products:
        return "We currently have no products available. Please check back later."
    header = f"*{brand} - Available Products:*"
    name_width = max(len(p.name) for p in products)
    unit_width = max(len(p.unit or "<") for p in products)
    pad = " " * 3
    rows = "\n".join(
        f"{p.name.ljust(name_width)}{pad}{p.unit.ljust(unit_width)}{pad}{_format_price(p.price)}"
        for p in products
    )
    note = "Reply with a product name for details, or ask to place an enquiry."
    return f"{header}\n\n```\n{rows}\n```\n\n{note}"


def product_price_msg(product) -> str:
    unit = f" for {product.unit}" if product.unit else ""
    return (
        f"*{product.name}*\n"
        f"Price: *{_format_price(product.price)}*{unit}\n"
        f"Category: {product.category or 'N/A'}\n\n"
        f"{product.description}"
    ).strip()


def delivery_available_msg(area: str) -> str:
    return (
        f"\u2705 *Yes! We deliver to {area}.*\n\n"
        f"Great news \u2014 {area} is within our delivery coverage. "
        f"You can place an order or enquiry and we'll get it to your door."
    )


def delivery_unavailable_msg(area: str) -> str:
    return (
        f"\u274c We're sorry, but we don't currently deliver to {area}.\n\n"
        f"Please check the area name or try a nearby locality. "
        f"You can also talk to our team for alternatives."
    )


def delivery_coverage_msg(brand: str, areas: list[str]) -> str:
    if not areas:
        return "We don't currently cover any delivery areas. Please check back later."
    bullets = "\n".join(f"\u2022 {area}" for area in areas)
    return (
        f"*{brand} - Areas We Deliver:*\n\n"
        f"{bullets}\n\n"
        f"Reply with an area name to check delivery or place an enquiry."
    )


def enquiry_captured_msg(enquiry_number: str, product_interest: str, area: str, brand: str) -> str:
    product = f" for *{product_interest}*" if product_interest else ""
    area_line = f" to *{area}*" if area else ""
    return (
        f"\U0001f4cb *Enquiry received!*\n\n"
        f"Reference: *{enquiry_number}*\n"
        f"Enquiry{product}{area_line}.\n\n"
        f"Thank you for reaching out to {brand}. Our team will contact you shortly \u23f3"
    )


def complaint_captured_msg(complaint_number: str, category: str, related_product: str, brand: str) -> str:
    cat = f" *{category.capitalize()}*" if category else ""
    product = f" regarding *{related_product}*" if related_product else ""
    return (
        f"\U0001f4a1 *Complaint received!*\n\n"
        f"Reference: *{complaint_number}*\n"
        f"Complaint{cat}{product}.\n\n"
        f"Thank you for letting us know, {brand}. Our team will look into this and get back to you shortly \u23f0"
    )


def complaint_in_progress_msg(brand: str) -> str:
    return (
        f"Thank you for reaching out again. We already have your complaint on record "
        f"and our team is looking into it \u23f0\n\n"
        f"We're sorry for the inconvenience. A support team member will contact you soon.\n\n"
        f"Is there anything else you need? \U0001f44d"
    )


def complaint_list_msg(brand: str, complaints: list) -> str:
    if not complaints:
        return "You have no complaints on record."
    lines = [f"*{brand} - Your Complaints:*"]
    for c in complaints:
        cat = c.category.capitalize() if c.category else "General"
        product = f" ({c.related_product})" if c.related_product else ""
        lines.append(f"{c.complaint_number}: {cat}{product} [{c.status}]")
    return "\n".join(lines)


def operator_handoff_msg() -> str:
    return (
        "Connecting you to our team. Please wait while we transfer you to a human agent. \u23f3"
    )


def render_reply(reply) -> str:
    """Render a structured agent reply to WhatsApp text.

    This is the single place messaging is formatted, so every session gets
    consistent output and the model can never invent raw pricing text.
    """
    kind = reply.type

    if kind == "text":
        return reply.message

    if kind == "product_list":
        return products_list_msg("Kabilai Dairy", reply.products)

    if kind == "product_price":
        if reply.unavailable:
            return (
                f"We don't currently have '{reply.product.name}' on our list. "
                f"Ask me to list all products."
            )
        return product_price_msg(reply.product)

    if kind == "delivery":
        return (
            delivery_available_msg(reply.area)
            if reply.available
            else delivery_unavailable_msg(reply.area)
        )

    if kind == "delivery_coverage":
        return delivery_coverage_msg("Kabilai Dairy", reply.areas)

    if kind == "company_info":
        c = reply.company
        lines = [f"*{c.name}*"]
        if c.address:
            lines.append(f"Address: {c.address}")
        if c.phone:
            lines.append(f"Phone: {c.phone}")
        if c.whatsapp_number:
            lines.append(f"WhatsApp: {c.whatsapp_number}")
        return "\n".join(lines)

    if kind == "enquiry_list":
        if not reply.enquiries:
            return "No enquiries found for this number."
        lines = ["*Your Enquiries:*"]
        for e in reply.enquiries:
            interest = e.product_interest or "General"
            area = f" \u2013 {e.delivery_area}" if e.delivery_area else ""
            lines.append(f"{e.enquiry_number}: {interest}{area} [{e.status}]")
        return "\n".join(lines)

    if kind == "enquiry_confirmed":
        return enquiry_captured_msg(
            reply.enquiry_number, reply.product_interest, reply.delivery_area, reply.brand
        )

    if kind == "complaint_confirmed":
        return complaint_captured_msg(
            reply.complaint_number, reply.category, reply.related_product, reply.brand
        )

    if kind == "complaint_in_progress":
        return complaint_in_progress_msg(reply.brand or "Kabilai Dairy")

    if kind == "complaint_list":
        return complaint_list_msg("Kabilai Dairy", reply.complaints)

    if kind == "handoff":
        return operator_handoff_msg()

    if kind == "help":
        return greeting_msg("Kabilai Dairy")

    return getattr(reply, "message", "")

