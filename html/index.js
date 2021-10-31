


class App {
    constructor () {
        this.ws = new WebSocket(websocketAddr);
        this.ws.onopen = () => {
            console.log('connected');
            this.addEventListener()
        };     
        this.ws.onerror = (err) => {
            console.log('error', err);      
            const buttons = document.getElementsByTagName('button')
            for (let button of buttons){
                button.disabled = true
            }

        };   
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

      const buttons = document.getElementsByTagName('button')
      for (let button of buttons){
          button.disabled = false
        button.addEventListener('click', (e) => {            
            this.send({
                action:'led.show',
                mode: e.target.id
            })

        })
      }
    
    }
}

const app = new App()