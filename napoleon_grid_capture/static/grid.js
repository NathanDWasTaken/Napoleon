console.log("%cHol' Up!", "font-family: Impact, fantasy; font-size : 70px");
console.log("%cChanging things here can mess up your current game!", "font-size : 15px");
console.log("%cAct with Caution!", "color: red; font-size : 25px; font-weight: 1000");
var columns = 4;
var rows = 4;
var lines = [];
var players = [];
var players_dict = {};
var player_turn_counter = 0;
var standart_gray = "rgb(211,211,211)";
function add_line(x1, y1, x2, y2, id, grid) {
    if (id === void 0) { id = "null"; }
    if (grid === void 0) { grid = false; }
    var newLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    var width = 8;
    var colour = standart_gray;
    if (id != "null") {
        newLine.setAttribute('id', id);
    }
    if (grid) {
        if (id.includes("s")) {
            x1 = x1 - width / 2;
            x2 = x2 + width / 2;
        }
        else if (id.includes("e")) {
            y1 = y1 - width / 2;
            y2 = y2 + width / 2;
        }
    }
    newLine.setAttribute('x1', x1.toString());
    newLine.setAttribute('y1', y1.toString());
    newLine.setAttribute('x2', x2.toString());
    newLine.setAttribute('y2', y2.toString());
    newLine.setAttribute("stroke", colour);
    newLine.setAttribute("stroke-width", width.toString());
    lines.push(newLine);
    return newLine;
}
function create_player(username, colour) {
    var player = new Player(username, colour);
    players.push(player);
    players_dict[username] = player;
    return player;
}
function add_player(username, colour) {
    create_player(username, colour);
    //Add to table
    var table = document.getElementById("score-board");
    var row = table.insertRow();
    row.id = "row-" + username;
    var cell = row.insertCell();
    var span = document.createElement("SPAN");
    span.setAttribute("color", colour);
    span.setAttribute("id", "name-" + username);
    var span_text = document.createTextNode(username);
    span.appendChild(span_text);
    cell.appendChild(span);
    cell = row.insertCell();
    span = document.createElement("SPAN");
    span.setAttribute("color", colour);
    span.setAttribute("id", "score-" + username);
    span_text = document.createTextNode("0");
    span.appendChild(span_text);
    cell.appendChild(span);
}
function rgb_to_rgba(rgb, a) {
    if (rgb.indexOf('a') == -1) {
        return rgb.replace(')', ", " + a + ")").replace('rgb', 'rgba');
    }
}
function createGrid() {
    var column_len = 50;
    var row_len = column_len;
    var svg_width = column_len * columns;
    var svg_height = row_len * rows;
    var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.id = "grid";
    svg.setAttribute("width", svg_width.toString());
    svg.setAttribute("height", svg_height.toString());
    // Create rectangles
    for (var row = 0; row < rows; row++) {
        for (var column = 1; column <= columns; column++) {
            var x = column * column_len;
            var y = row * row_len;
            var newRect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            newRect.id = column - 1 + "-" + row;
            newRect.setAttribute("width", column_len.toString());
            newRect.setAttribute("height", row_len.toString());
            newRect.setAttribute("x", (x - column_len).toString());
            newRect.setAttribute("y", y.toString());
            newRect.setAttribute("fill", "none");
            newRect.setAttribute("opacity", "0");
            svg.appendChild(newRect);
        }
    }
    // Create vertical Lines
    for (row = 0; row < rows; row++) {
        for (column = 1; column < columns; column++) {
            var x = column * column_len;
            var y = row * row_len;
            var newLine = add_line(x, y, x, y + row_len, column - 1 + "-" + row + "-e", true);
            newLine.setAttribute("marked", "false");
            svg.appendChild(newLine);
            lines.push(newLine);
        }
    }
    // Create Horizontal Lines
    for (column = 0; column < columns; column++) {
        for (row = 1; row < rows; row++) {
            var x = column * column_len;
            var y = row * row_len;
            var newLine = add_line(x, y, x + column_len, y, column + "-" + (row - 1) + "-s", true);
            newLine.setAttribute("marked", "false");
            svg.appendChild(newLine);
            lines.push(newLine);
        }
    }
    document.getElementById("main-container").appendChild(svg);
    lines.forEach(function (line) {
        var svg = document.getElementById("grid");
        line.addEventListener('mouseenter', function (event) {
            var old_highlight = document.getElementById("highlighted");
            if (old_highlight != null) {
                old_highlight.remove();
            }
            if (line.getAttribute("marked") == "false") {
                make_highlight(line.id, players[player_turn_counter].colour);
            }
        });
    });
    // Create the border
    svg.appendChild(add_line(0, 0, 0, svg_height));
    svg.appendChild(add_line(0, 0, svg_width, 0));
    svg.appendChild(add_line(0, svg_height, svg_width, svg_height));
    svg.appendChild(add_line(svg_width, 0, svg_width, svg_height));
}
function create_random_username(length) {
    var result = '';
    var characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    var charactersLength = characters.length;
    for (var i = 0; i < length; i++) {
        result += characters.charAt(Math.floor(Math.random() * charactersLength));
    }
    return result;
}
function make_highlight(line_id, player_colour) {
    // @ts-ignore
    if ((multiplayer && my_turn) || !multiplayer) {
        var svg = document.getElementById("grid");
        var line_1 = document.getElementById(line_id);
        var x1 = parseInt(line_1.getAttribute("x1"));
        var y1 = parseInt(line_1.getAttribute("y1"));
        var x2 = parseInt(line_1.getAttribute("x2"));
        var y2 = parseInt(line_1.getAttribute("y2"));
        var highlight_1 = add_line(x1, y1, x2, y2, "highlighted");
        highlight_1.setAttribute("stroke-width", "12");
        highlight_1.setAttribute("stroke", player_colour);
        highlight_1.addEventListener('mouseleave', function (event) {
            highlight_1.remove();
        });
        highlight_1.addEventListener('click', function (event) {
            if (line_1.getAttribute("marked") == "false") {
                var player = players[player_turn_counter];
                var next_player = players[(player_turn_counter + 1) % players.length];
                // make a move
                // @ts-ignore
                gameSocket.send(JSON.stringify({
                    'command': 'make move',
                    'wall': line_1.id,
                    'colour': player.colour,
                    'player': player.username,
                    'next player': next_player.username,
                    'next colour': next_player.colour
                }));
            }
        });
        svg.appendChild(highlight_1);
    }
}
function update_scoreboard(username, score) {
    document.getElementById("score-" + username).innerText = score;
}
function victory(player_results) {
    var results = [];
    for (var index in player_results) {
        var tuple = player_results[index];
        var player = players_dict[tuple[0]];
        player.score = tuple[1];
        results.push(player);
    }
    var winners = [results[0]];
    var max_score = results[0].score;
    for (var key = 1; key < results.length - 1; key++) {
        var player = results[key];
        if (player.score == max_score) {
            winners.push(player);
        }
        else
            break;
    }
    if (winners.length == 1) {
        var winner = winners[0];
        var winning_div = document.createElement("div");
        winning_div.id = "winning-screen";
        winning_div.style.backgroundColor = rgb_to_rgba(winner.colour, "0.5");
        var font = document.createElement("font");
        font.id = "winning-message";
        font.innerText = winner.username + " won!";
        winning_div.appendChild(font);
        document.getElementById("main-container").remove();
        document.body.appendChild(winning_div);
    }
}
var Player = /** @class */ (function () {
    function Player(username, colour) {
        this.username = username;
        this.colour = colour;
        this.score = 0;
    }
    return Player;
}());
