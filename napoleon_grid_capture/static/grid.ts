console.log("%cHol' Up!", "font-family: Impact, fantasy; font-size : 70px");
console.log("%cChanging things here can mess up your current game!", "font-size : 15px")
console.log("%cAct with Caution!", "color: red; font-size : 25px; font-weight: 1000")

let columns = 4
let rows = 4

let lines = []

let players = []
let players_dict = {}
var player_turn_counter = 0

const standart_gray = "rgb(211,211,211)"



function add_line(x1 : number, y1 : number, x2 : number, y2 : number, id : string = "null", grid : boolean = false) {
    var newLine = document.createElementNS('http://www.w3.org/2000/svg','line');

    let width = 8
    let colour = standart_gray
    if (id != "null") {
        newLine.setAttribute('id', id);
    }

    if (grid) {
        if (id.includes("s")) {
            x1 = x1 - width / 2
            x2 = x2 + width / 2
        }

        else if (id.includes("e")) {
            y1 = y1 - width / 2
            y2 = y2 + width / 2
        }
    }

    newLine.setAttribute('x1', x1.toString());
    newLine.setAttribute('y1', y1.toString());
    newLine.setAttribute('x2', x2.toString());
    newLine.setAttribute('y2', y2.toString());
    newLine.setAttribute("stroke", colour)
    newLine.setAttribute("stroke-width", width.toString())

    lines.push(newLine)
    return newLine
}

function create_player(username, colour) {
    var player = new Player(username, colour)
    players.push(player)
    players_dict[username] = player

    return player
}

function add_player(username, colour) {
    create_player(username, colour)

    //Add to table
    const table = document.getElementById("score-board") as HTMLTableElement
    let row = table.insertRow()
    row.id = `row-${username}`

    let cell = row.insertCell()
    var span = document.createElement("SPAN") as HTMLSpanElement
    span.setAttribute("color", colour)
    span.setAttribute("id", `name-${username}`)
    var span_text = document.createTextNode(username)

    span.appendChild(span_text)
    cell.appendChild(span)


    cell = row.insertCell()
    span = document.createElement("SPAN") as HTMLSpanElement
    span.setAttribute("color", colour)
    span.setAttribute("id", `score-${username}`)
    span_text = document.createTextNode("0")

    span.appendChild(span_text)
    cell.appendChild(span)
}

function rgb_to_rgba(rgb, a) {
    if(rgb.indexOf('a') == -1) {
        return rgb.replace(')', `, ${a})`).replace('rgb', 'rgba');
    }
}


function createGrid() {
    let column_len = 50
    let row_len = column_len

    let svg_width = column_len * columns
    let svg_height = row_len * rows


    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.id = "grid"

    svg.setAttribute("width", svg_width.toString());
    svg.setAttribute("height", svg_height.toString());
    
    // Create rectangles
    for (var row = 0; row < rows; row++) {
        for (var column = 1; column <= columns; column++) {
            let x = column * column_len
            let y = row * row_len

            const newRect = document.createElementNS('http://www.w3.org/2000/svg','rect');
            newRect.id = `${column-1}-${row}`
            newRect.setAttribute("width", column_len.toString())
            newRect.setAttribute("height", row_len.toString())
            newRect.setAttribute("x", (x-column_len).toString())
            newRect.setAttribute("y", y.toString())
            newRect.setAttribute("fill", "none")
            newRect.setAttribute("opacity", "0")
            svg.appendChild(newRect)
        }
    }
    
    // Create vertical Lines
    for (row = 0; row < rows; row++) {
        for (column = 1; column < columns; column++) {
            let x = column * column_len
            let y = row * row_len

            const newLine = add_line(x, y, x, y + row_len, `${column-1}-${row}-e`, true)
            newLine.setAttribute("marked", "false")
            svg.appendChild(newLine)

            lines.push(newLine)
        }
    }

    // Create Horizontal Lines
    for (column = 0; column < columns; column++) {
        for (row = 1; row < rows; row++) {

            let x = column * column_len
            let y = row * row_len

            const newLine = add_line(x, y, x + column_len, y, `${column}-${row-1}-s`, true)
            newLine.setAttribute("marked", "false")
            svg.appendChild(newLine)

            lines.push(newLine)
        }
    }


    document.getElementById("main-container").appendChild(svg)



    lines.forEach(function(line){
        const svg = document.getElementById("grid")
        

        line.addEventListener('mouseenter', function (event) {
            const old_highlight = document.getElementById("highlighted")
            if (old_highlight != null) {old_highlight.remove()}

            if (line.getAttribute("marked") == "false") {
                make_highlight(line.id, players[player_turn_counter].colour)
            }
        })
    })

    // Create the border
    svg.appendChild(add_line(0, 0, 0, svg_height))
    svg.appendChild(add_line(0, 0, svg_width, 0))
    svg.appendChild(add_line(0, svg_height, svg_width, svg_height))
    svg.appendChild(add_line(svg_width, 0, svg_width, svg_height))
}

function create_random_username(length) {
    var result           = '';
    var characters       = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    var charactersLength = characters.length;
    for ( var i = 0; i < length; i++ ) {
        result += characters.charAt(Math.floor(Math.random() * charactersLength));
    }
    return result;
}

function make_highlight(line_id : string, player_colour : string) {
    // @ts-ignore
    if ((multiplayer && my_turn) || !multiplayer) {
        const svg = document.getElementById("grid")

        const line = document.getElementById(line_id)
        const x1 = parseInt(line.getAttribute("x1"))
        const y1 = parseInt(line.getAttribute("y1"))
        const x2 = parseInt(line.getAttribute("x2"))
        const y2 = parseInt(line.getAttribute("y2"))

        const highlight = add_line(x1, y1, x2, y2, "highlighted")
        highlight.setAttribute("stroke-width", "12")
        highlight.setAttribute("stroke", player_colour)

        highlight.addEventListener('mouseleave', function (event) {
            highlight.remove()
        })

        highlight.addEventListener('click', function (event) {
            if (line.getAttribute("marked") == "false") {

                let player = players[player_turn_counter]
                let next_player = players[(player_turn_counter + 1) % players.length]

                // make a move
                // @ts-ignore
                gameSocket.send(JSON.stringify({
                    'command' : 'make move',
                    'wall': line.id,
                    'colour' : player.colour,
                    'player' : player.username,
                    'next player' : next_player.username,
                    'next colour' : next_player.colour
                }));
            }
        })
        svg.appendChild(highlight)
    }
}

function update_scoreboard(username, score) {
    document.getElementById(`score-${username}`).innerText = score
}

function victory(player_results) {
    let results = []

    for (const index in player_results) {
        let tuple = player_results[index]
        let player = players_dict[tuple[0]]
        player.score = tuple[1]
        results.push(player)
    }

    const winners = [results[0]]
    const max_score = results[0].score
    for (var key = 1; key < results.length -1; key++) {
        let player = results[key]

        if (player.score == max_score) {
            winners.push(player)
        }
        else break
    }

    if (winners.length == 1) {
        let winner = winners[0]
        const winning_div = document.createElement("div")
        winning_div.id = "winning-screen"

        winning_div.style.backgroundColor = rgb_to_rgba(winner.colour, "0.5")
        

        const font = document.createElement("font")
        font.id = "winning-message"
        font.innerText = `${winner.username} won!`
        winning_div.appendChild(font)
        

        document.getElementById("main-container").remove()

        document.body.appendChild(winning_div)
    }
}

class Player {
    username : string
    colour : string
    score : number

    constructor(username : string, colour : string) {
        this.username = username;
        this.colour = colour;
        this.score = 0;
    }
}