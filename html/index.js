console.log('hellow js!')

var $ = document.getElementById.bind(document)

class App {
    constructor () {
        this.ws = new WebSocket(websocketAddr);
        this.addEventListener()
    }
    
    send(msg) {        
        if (this.ws && this.ws.readyState == 1) {
          this.ws.send(JSON.stringify(msg));
          console.log('send:', msg)
          return true;
        }
        return false;
      }

    addEventListener (){

        $('mode1').addEventListener('click', () => {
            this.send({
                action: 'led.show',
                mode: 'toogle mode 1'
            })
        })

    
    
    
    
    }
}

const app = new App()