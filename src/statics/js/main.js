window.onload = function() {
  const themeColor = "#850491";
  const host = location.host;
  const url = "ws://"+host+"/connect";

  function getLocalSettings(){
    const localSettingsStr = localStorage.getItem("settings");
    localSettings = JSON.parse(localSettingsStr)? JSON.parse(localSettingsStr): {};
    return localSettings
  }

  function setLocalSettings(key, value){
    const localSettings = getLocalSettings();
    localSettings[key] = value
    localStorage.setItem("settings", JSON.stringify(localSettings));
  }



  axios.get("statics/i18n/main.json")
    .then((res) => {

  var localSettings = getLocalSettings();

  if(localSettings["language"]){
    var language = localSettings["language"]
  }else{
    var language = (window.navigator.languages && window.navigator.languages[0]) ||
                    window.navigator.language ||
                    window.navigator.userLanguage ||
                    window.navigator.browserLanguage;
    language = language? language.split("-")[0]: "en"
    setLocalSettings("language", language);
  }

  if(localSettings["imagesPerPage"]){
    var imagesPerPage = parseInt(localSettings["imagesPerPage"]);
  }else{
    var imagesPerPage = 10;
    setLocalSettings("imagesPerPage", imagesPerPage);
  }

  const translations = res.data;
  Vue.use(VueI18n);
  Vue.use(VueCharts);
  const i18n = new VueI18n({
    locale: language,
    messages: translations
  });

  let vm = new Vue({
    delimiters: ['${', '}'],
    i18n: i18n,
    el: '#app',
    data: {
      themeColor: themeColor,
      ws : new WebSocket(url),
      recipes: [],
      models: [],
      learningData: [],
      selectedRecipe: "",
      selectedModel: "",
      selectedLearningData: "",
      inferenceLabels: ["0","1","2","3", "4", "5", "6", "7", "8", "9"],
      classficationResult: [],
      vectorizationResult: [],
      dimRedResult: [],
      recipeFields: {},
      dataFields: {},
      modelFields: {},
      newData: {
        name: "",
        description: ""
      },
      newRecipe: {},
      newModel: {
        name: "",
        description: "",
        charts: [],
        config: {
          "learning_rate": 0.001,
          "batch_size": 64,
          "epoch": 0.05,
          "data": {
            "ratio": 0.1
          },
          "saver": {
            "evaluate_every": {
              "train": 10,
              "test": 30
            },
            "num_checkpoints": 5
          }
        }
      },
      recipeLayers: [],
      learningProgress: 0,
      learningNumIter: 0,
      uploadFile: null,
      inferenceData: null,
      showAddData: false,
      showAddRecipe: false,
      languageOptions: [],
      activationOptions:[],
      inferenceTypeOptions: [],
      selectedMenu: "data",
      selectedLanguage: language,
      dataSortBy: "updateTime",
      dataSortDesc: true,
      imagesPerPage: imagesPerPage,
      selectedInferenceFile: "",
      inferencePreviewImg: "",
      selectedInferenceType: "",
      chartOptions: {responsive: false, maintainAspectRatio: false},
      uploaded: false,
      progress: 0,
      uploadInferenceZipProgress: 0,
      result: ""
    },
    methods: {
      addChartData: function(charts, label, newLabel, newData){
        const index = this.getTargetChartIndex(charts, label)
        const chartData = charts[index];
        let data = Object.assign({}, chartData);
        data.labels.push(newLabel)
        const newDataNum = parseFloat(newData);
        data.datasets[0].data.push(newDataNum);
        charts[index] = data;
      },
      getTargetChartIndex: function(charts, label){
        for(let i=0; i < charts.length; i++){
          const chart = charts[i];
          if(chart.datasets[0].label == label){
            return i;
          }
        }
      },
      initRecipeLayers: function(){
        this.recipeLayers = [
          {
            "name": "inputData",
            "type": "input",
            "params": {
              "dataWidth": 28,
              "dataHeight": 28,
                "channel": 0
            },
            "graph": {}
          },
          {
            "name": "inputLabels",
            "type": "input",
            "params": {
              "nClass": 10
            },
            "graph": {}
          },
          {
            "name": "conv2d",
            "type": "layer",
            "params": {
              "act": "relu",
              "outSize": 32
            },
            "graph": {}
          },
          {
            "name": "max_pool",
            "type": "layer",
            "graph": {}
          },
          {
            "name": "fc",
            "type": "layer",
            "params": {
              "act": "ident",
              "outSize": 10
            },
            "graph": {}
          },
          {
            "name": "flatten",
            "type": "layer",
            "graph": {}
          },
          {
            "name": "reshape",
            "type": "layer",
            "params": {
              "shape": [ -1, 28, 28, 1]
            },
            "graph": {}
          }
        ];
      },
      initCharts: function(model, chartData){
        const labels = [
          {label: "train_accuracy", color: themeColor},
          {label: "train_loss", color: themeColor},
          {label: "test_accuracy", color: "#f87979"},
          {label: "test_loss", color: "#f87979"}
        ]
        const charts = [];
        labels.forEach(v=>{
          typeTag = v.label.split("_")
          if (chartData && chartData[typeTag[0]][typeTag[1]]){
            var labels = chartData[typeTag[0]].step;
            var data = chartData[typeTag[0]][typeTag[1]];
          }else{
            var labels = [];
            var data = [];
          }
          const c = {
            labels: labels,
            datasets: [
              {
                label: v.label,
                fill: false,
                backgroundColor: v.color,
                data: data
              }
            ]
          };
          charts.push(c)
        });
        model.charts = charts;
      },
      linkGen: function(row){
        console.log(row.item);
        const page = row.item.currentPage;
        if(page != row.item.prevPage){
          const req = {
            action: "getData",
            dataId: row.item.id,
            offset: (page-1) * this.imagesPerPage,
            limit: page * this.imagesPerPage
          };
          this.sendMessage(req);
          row.item.prevPage = page;
        }
      },
      toggleData: function(row){
        if(!row.detailsShowing){
          console.log(row.item.id);
          const req = {
            action: "getData",
            dataId: row.item.id,
            offset: 0,
            limit: this.imagesPerPage
          }
          this.sendMessage(req);
        }
        row.toggleDetails();
      },
      resetZoom: function(recipe){
        recipe.graph.zoom(1.0);
      },
      resetPan: function(recipe){
        recipe.graph.pan({x:0,y:0});
      },
      deleteEdge: function(row){
        if(row.hasClass("realNode")){
          const edges = row.neighborhood("edge");
          const deleteTargetId = row.data().id;
          console.log(deleteTargetId);
          for(let i=0; i<edges.length; i++){
            if(edges[i].data().target == deleteTargetId){
              const id = edges[i].data().id;
              this.newRecipe.graph.remove("#"+id);
              console.log(id);
              break;
            }
          }
        }else{
          const id = row.data().id;
          this.newRecipe.graph.remove("#"+id);
        }
      },
      deleteNode: function(id){
        console.log(id);
        this.newRecipe.graph.remove("#"+id);
        this.newRecipe.tappedLayer = this.createEmptyLayer();
      },
      createEmptyLayer: function(){
        const layer = {
          data: () => {
            return {
              name: ""
            };
          },
          neighborhood: (selecter) => {
            return [];
          }
        };
        return layer
      },
      initNewRecipe: function(){
        console.log("init newRecipe");
        this.newRecipe = {
          tappedLayer: this.createEmptyLayer(),
          info: {
            name: "",
            description: "",
            graph: {}
          },
          layers: [
            {
              id: 0,
              name: "inputData",
              params: {
                "dataWidth": 28,
                "dataHeight": 28,
                "channel": 0
              },
              graph:{
                position: {x: 150, y: 100}
              }
            },
            { id: 1,
              name: "loss",
              graph: {
                position: {x: 250, y: 200}
              }
            },
            {
              id: 2,
              name: "acc",
              graph: {
                position: {x: 350, y: 200}
              }
            }
          ],
          edges: [],
          train: {}
        };
      },
      clickNode: function(graph, pureNode){
        const node = pureNode.data();
        const id = node.id;
        const p = pureNode.position()
        const nodeId =  new Date().getTime();
        const edgeId = "edge-"+id+"-"+nodeId;

        const edge = {
          data: {
            id: edgeId,
            source: id,
            target: nodeId
          }
        };

        const targetNode =  {
          data: {
            id: nodeId,
            name: "*",
            weight: 10,
            height: "1px",
            isConnectPoint: true,

            faveShape: "ellipse",
            faveColor: this.themeColor
          },
          position: {x: p.x + 20, y: p.y + 50}
        };

        graph.add(targetNode)

        graph.nodes().on("free", (e)=>{
          const connectPoint = e.target;
          if(connectPoint.data().isConnectPoint){
            const connectPointId = connectPoint.data().id
            const targetPosition = connectPoint.position();
            const nodes = graph.elements("node");
            nodes.forEach(v=>{
              const id = v.data().id;
              const position = v.position();
              if(position && id != connectPointId){
                const width = v.width();
                const height = v.height();
                if((position.x - width/2) <= targetPosition.x && targetPosition.x <= (position.x + width/2)
                  && (position.y - height/2) <= targetPosition.y && targetPosition.y <= (position.y + height/2)){

                  const sourceNode = connectPoint.neighborhood("node")[0];
                  if(sourceNode){
                    const sourceId = sourceNode.data().id;
                    graph.remove("#"+connectPointId);
                    const edgeId = new Date().getTime();
                    const edge = {
                      data: {
                        id: edgeId,
                        source: sourceId,
                        target: id
                      }
                    };
                    graph.add(edge);
                  }

                }
              }
            });
          }
        });

        graph.add(edge);

      },
      createGraphNode(id, name, position, recipe){
        console.log("createGraphNode");
        console.log(recipe);
        recipe.graph.faveColor = this.themeColor;
        recipe.graph.faveShape = "rectangle";
        const data = Object.assign({
            id: id,
            name: name,
            params: recipe.params,
          },
          recipe.graph
        );
        const node =  {
          data: data,
          classes: "realNode",
          position: position
        };
        return node;
      },
      onEnd: function(e){
        const graph = this.newRecipe.graph;
        const name = e.clone.innerText.trim();
        const newNodeId = graph.nodes(".realNode").length;
        console.log(newNodeId);
        const position = {x: 100, y: 100};
        let data = null;
        for(let i=0; i< this.recipeLayers.length; i++){
          if(this.recipeLayers[i].name == name){
            data = JSON.parse(JSON.stringify(this.recipeLayers[i]));
            break;
          }
        }
        const node = this.createGraphNode(newNodeId, name, position, data)
        graph.add(node);

        graph.$("#"+newNodeId).on("tap", (e)=>{
          if(this.newRecipe.tappedLayer.removeClass){
            this.newRecipe.tappedLayer.removeClass("selected");
          }
          const node = e.target;
          node.addClass("selected");
          this.newRecipe.tappedLayer = node;
        });
      },
      addRecipe: function(){
        const recipe = this.createRecipe(this.newRecipe);
        console.log(recipe);
        const req = {
          action: "addRecipe",
          recipe: recipe
        }
        this.sendMessage(req);
      },
      toggleRecipe: function(row){
        if(!row.detailsShowing){
          this.showRecipe(row);
        }else{
          this.closeRecipe(row);
        }
      },
      showRecipe: function(row){
        row.toggleDetails();
        this.$nextTick(()=>{
          this.buildGraph(row.item.body, row.index);
          row.item.body.graph.autolock(true);
          row.item.body.graph.zoomingEnabled(false);
          row.item.body.graph.panningEnabled(false);
        });
      },

      createRecipe: function(recipe){
        console.log("#######");
        console.log(recipe);
        console.log("#######");
        const nodes = recipe.graph.elements("node");
        const graphEdges = recipe.graph.elements("edge");

        const layers = [];
        nodes.forEach(v=>{
          if(v.position){
            console.log(v.data().id);
            const data = v.data();
            const layer = {
              id: data.id,
              name: data.name,
              params: data.params,
              graph: {
                position: v.position(),
                width: v.width(),
                height: v.height(),
              }
            }
            layers.push(layer);
          }
        });
        recipe.layers = layers;

        const edges = []
        graphEdges.forEach(v=>{
          const edge = {
            sourceId: v.data().source,
            targetId: v.data().target
          }
          edges.push(edge);
        });
        recipe.edges = edges;

        recipe.info.graph = {
          zoom: recipe.graph.zoom(),
          pan: recipe.graph.pan()
        };
        delete recipe.graph;
        delete recipe.tappedLayer;
        return recipe;
      },

      closeRecipe: function(row){
        const recipe = row.item.body;
        row.item.body = this.createRecipe(recipe);
        row.toggleDetails();
      },
      buildGraph: function(body, index){
        const layers = body.layers;
        const edges = body.edges;
        const graph = body.info.graph;
        const elem = document.getElementById("cy"+index);
        const layoutOptions = {
          directed: true,
          padding: 10,
          name: 'breadthfirst'
        };
        const cy = cytoscape({
          container: elem,
          elements: [],
          style: [
            {
              selector: 'edge',
              style: {
                'curve-style': 'bezier',
                'target-arrow-shape': 'triangle',
                'width': 4,
                'line-color': '#ddd',
                'target-arrow-color': '#ddd'
              }
            },
            {
              selector: 'node',
              style: {
                shape: "data(faveShape)",
                //width: 'mapData(weight, 40, 80, 20, 60)',
                width: 'label',
                label: 'data(name)',
                color: "#fff",
                'text-outline-width': 2,
                'text-outline-color': 'data(faveColor)',
                'background-color': 'data(faveColor)',
                'text-valign': 'center',
                'text-halign': 'center'
              }
            },
            {
              selector: "node.selected",
              style: {
                'border-color': '#f44242',
                'border-width': 3,
                'border-opacity': 0.8
              }
            }
          ],
          layout: layoutOptions
        });
        layers.forEach(v=>{
          const node = this.createGraphNode(v.id, v.name, v.graph.position, v);
          cy.add(node);
        });
        edges.forEach((e, i)=>{
          const edge = {
            data: {
              id: 'edge' + i,
              source: e.sourceId,
              target: e.targetId
            }
          };
          cy.add(edge);
        });
        const layout = cy.elements().layout(layoutOptions);
        if(layers.length ==0 || !layers[0].graph.position){
         console.log("set postions from dfs.");
         layout.run();
        }else{
          console.log("set postions from data.");
          if(graph && graph.zoom && graph.pan){
            console.log("zoom:"+graph.zoom);
            console.log("pan x:"+graph.pan.x);
            console.log("pan y:"+graph.pan.y);
            cy.pan(graph.pan);
            cy.zoom(graph.zoom);
          }
        }
        cy.nodes().on("tap", (e)=>{
          if(body.tappedLayer.removeClass){
            body.tappedLayer.removeClass("selected");
          }
          const node = e.target;
          node.addClass('selected');
          body.tappedLayer = node;
        });
        body.graph = cy;

      },
      parseFile: function(file, chunkSize){
        var fileSize = file.size;
        var reader = new FileReader();

        reader.onload = (e) =>{
          var body = e.target.result;
          for(var i = 0; i < fileSize; i += chunkSize) {
            var chunk = body.slice(i, chunkSize + i);
            this.ws.send(chunk);
          }
        };
        reader.readAsArrayBuffer(file)
      },
      deleteRecipe: function(row){
        const recipeId = row.item.id;
        console.log(recipeId);
        const req = {
          action: "deleteRecipe",
          recipeId: recipeId
        }
        this.sendMessage(req)
      },
      deleteModel: function(row){
        const id = row.item.id;
        console.log(id);
        const req = {
          action: "deleteModel",
          modelId: id
        }
        this.sendMessage(req)
      },
      deleteData: function(row){
        const dataId = row.item.id;
        console.log(dataId);
        const req = {
          action: "deleteData",
          dataId: dataId
        }
        this.sendMessage(req)
      },
      changeMenu: function(menu){
        this.setRecipeFields();
        this.setDataFields();
        this.setModelFields();
        this.setActivationOptions();
        this.setInferenceTypeOptions();
        this.selectedMenu = menu;
      },
      changeLang: function(lang){
        this.selectedLanguage = lang;
      },
      startLearning: function(){
        this.initCharts(this.newModel);
        const config = this.newModel.config;
        const info = {
          name: this.newModel.name,
          description: this.newModel.description
        };
        req = {
          "action": "startLearning",
          "recipeId": this.selectedRecipe["id"],
          "dataId": this.selectedLearningData["id"],
          "info": info,
          "trainConfig": config
        }
        this.sendMessage(req)

      },
      selectedFile: function(e){
        e.preventDefault();
        let files = e.target.files;
        this.uploadFile = files[0];
      },
      dragChoose: function(e){
        e.target.className = "scroll";
      },
      dragEnd: function(e){
        console.log("end");
        e.target.className = "";
      },
      dragBlur: function(e){
        console.log("blur");
        e.target.className = "";
      },
      uploadData: function(){
        const fileSize = this.uploadFile.size;
        const request = {
          action: "startUploading",
          name: this.newData.name,
          description: this.newData.description,
          fileSize: fileSize
        };
        this.progress = 1;
        this.sendMessage(request);
      },
      updateData: function(data){
        const req = {
          action: "updateData",
          dataInfo: {
            "name": data.name,
            "description": data.description
          },
          dataId: data.id
        };
        this.sendMessage(req)
        data.mode = "detail";
      },
      cancelData: function(data){
        data.name = data.bkup.name;
        data.description = data.bkup.description;
        data.mode = "detail";
      },
      updateModel: function(data){
        const req = {
          action: "updateModel",
          model: {
            "name": data.name,
            "description": data.description
          },
          modelId: data.id
        };
        this.sendMessage(req)
        data.mode = "detail";
      },
      cancelModel: function(data){
        data.name = data.bkup.name;
        data.description = data.bkup.description;
        data.mode = "detail";
      },
      updateList: function(targetList, targetItem, optionDict){
        const updateId = this.getTargetIndex(targetList, targetItem.id);
        targetItem.mode = "detail";
        targetItem.bkup = Object.assign({}, targetItem);
        if(optionDict){
          for(let i=0; i < optionDict.length; i++){
            const option = optionDict[i]
            targetItem[option.key] = option.value;
          }
        }
        this.$set(targetList, updateId, targetItem);
      },
      selectInferenceFile: function(e){
        e.preventDefault();
        this.inferencePreviewImg = "";
        this.classficationResult = [];
        this.vectorizationResult = [];
        this.uploadInferenceZipProgress = 0
        const files = e.target.files;
        this.selectedInferenceFile = files[0];
        const ext = this.selectedInferenceFile.name.split(".")[1]
        if(ext != "zip"){
          reader = new FileReader();
          reader.onload = e => {
            this.inferencePreviewImg = e.target.result;
          };
          reader.readAsDataURL(this.selectedInferenceFile);
        }

        reader = new FileReader();
        reader.onload = e => {
          this.inferenceData = e.target.result;
          const req = {
            "action": "inferenceImages",
            "type": this.selectedInferenceType,
            "modelId": this.selectedModel.id,
            "recipeId": this.selectedModel.recipeId,
            "fileName": this.selectedInferenceFile.name,
            "fileSize": this.selectedInferenceFile.size
          };
          this.sendMessage(req);
        };
        reader.readAsArrayBuffer(this.selectedInferenceFile);
      },
      sendInferenceData: function(){
        this.ws.send(this.inferenceData);
      },
      updateRecipe: function(data){
        const req = {
          action: "updateRecipe",
          info: {
            "name": data.body.info.name,
            "description": data.body.info.description
          },
          recipeId: data.id
        };
        this.sendMessage(req)
        data.mode = "detail";
      },
      cancelRecipe: function(data){
        data.body.info.name = data.bkup.body.info.name;
        data.body.info.description = data.bkup.body.info.description;
        data.mode = "detail";
      },
      sendMessage: function(msg){
        console.log(msg);
        this.ws.send(JSON.stringify(msg));
      },
      json2String: function(json){
        console.log(json);
        return JSON.stringify(json, undefined, 4);
      },
      setInferenceTypeOptions: function(){
        this.inferenceTypeOptions = [
          {value: "classification", text: i18n.t("inference.classification")},
          {value: "regression", text: i18n.t("inference.regression")},
          {value: "vectorization", text: i18n.t("inference.vectorization")},
          {value: "dimRed", text: i18n.t("inference.dimRed")}
        ];
      },
      setActivationOptions: function(){
        this.activationOptions = [
          {value: "relu", text: "ReLU"},
          {value: "ident", text: i18n.t("activation.ident")}
        ];
      },
      show2D: function(data){
        /*
        var data = [
          {
            "imageName": "@name@",
            "vector":[ -6.258190828419952, -21.277623406861302],
            "body": "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a\nHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAAcABwBAREA/8QAHwAAAQUBAQEB\nAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1Fh\nByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZ\nWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXG\nx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/9oACAEBAAA/APn+iiituw8LandzH7Rb\nT2VqiebLczwPtRMgA4AyxJKgAdSR0HNdBbeDvD+qyLa6fq99bXbDCLqFoUEjemRwOfcn0zXO654U\n1vw7qL2OpadPFKOVbyyVkH95TjkVmNa3CEboJRnnlDV+DxPrtqEEGsX0YT7m2dht+nNXP+E78V7S\nreIdRYHqHnLZ6+v1pU8eeKkTYuuXYXqV3cH8Pwqpc+KNcvJFe41S5dlXaDvxx17fWsiiiiv/2Q==\n"
          }];
          */
        var margin = { top: 50, right: 300, bottom: 50, left: 50 },
            //outerWidth = 1050,
            //outerHeight = 500,
            outerWidth = screen.width-100,
            outerHeight = screen.height-200;
            width = outerWidth - margin.left - margin.right,
            height = outerHeight - margin.top - margin.bottom;

        var x = d3.scale.linear().range([0, width]).nice();

        var y = d3.scale.linear().range([height, 0]).nice();

        var xCat = "x",
            yCat = "y",
            rCat = "x"
            colorCat = "Manufacturer";

          data.forEach(function(d) {
               d.vector[0] = +d.vector[0];
               d.vector[1] = +d.vector[1];
          });

          var xMax = d3.max(data, function(d) { return d.vector[0]; }) * 1.05,
              xMin = d3.min(data, function(d) { return d.vector[0]; }),
              xMin = xMin > 0 ? 0 : xMin,
              yMax = d3.max(data, function(d) { return d.vector[1]; }) * 1.05,
              yMin = d3.min(data, function(d) { return d.vector[1]; }),
              yMin = yMin > 0 ? 0 : yMin;

          x.domain([xMin, xMax]);
          y.domain([yMin, yMax]);

          var xAxis = d3.svg.axis()
              .scale(x)
              .orient("bottom")
              .tickSize(-height);

          var yAxis = d3.svg.axis()
              .scale(y)
              .orient("left")
              .tickSize(-width);

          var color = d3.scale.category10();

          var tip = d3.tip()
              .attr("class", "d3-tip")
              .offset([-10, 0])
              .html(function(d) {
                return d.imageName + "<br/>"+ "x: " + d.vector[0] + "<br>" + "y: " + d.vector[1];
              });

          var zoomBeh = d3.behavior.zoom()
              .x(x)
              .y(y)
              .scaleExtent([0, 500])
              .on("zoom", zoom);

          var svg = d3.select("#scatter")
            .append("svg")
              .attr("width", outerWidth)
              .attr("height", outerHeight)
            .append("g")
              .attr("transform", "translate(" + margin.left + "," + margin.top + ")")
              .call(zoomBeh);

          svg.call(tip);

          svg.append("rect")
              .attr("width", width)
              .attr("height", height);

          svg.append("g")
              .classed("x axis", true)
              .attr("transform", "translate(0," + height + ")")
              .call(xAxis)
            .append("text")
              .classed("label", true)
              .attr("x", width)
              .attr("y", margin.bottom - 10)
              .style("text-anchor", "end")

          svg.append("g")
              .classed("y axis", true)
              .call(yAxis)
            .append("text")
              .classed("label", true)
              .attr("transform", "rotate(-90)")
              .attr("y", -margin.left)
              .attr("dy", ".71em")
              .style("text-anchor", "end")

          var objects = svg.append("svg")
              .classed("objects", true)
              .attr("width", width)
              .attr("height", height);

          objects.append("svg:line")
              .classed("axisLine hAxisLine", true)
              .attr("x1", 0)
              .attr("y1", 0)
              .attr("x2", width)
              .attr("y2", 0)
              .attr("transform", "translate(0," + height + ")");

          objects.append("svg:line")
              .classed("axisLine vAxisLine", true)
              .attr("x1", 0)
              .attr("y1", 0)
              .attr("x2", 0)
              .attr("y2", height);

          objects.selectAll(".dot")
              .data(data)
              .enter()
              .append("svg:image")
              .classed("dot", true)
              .attr("dy", ".5em")
              .attr("transform", transform)
              .attr("xlink:href", function(d){
                  //var name = d.vocab.split("/")[2];
                  //var url= "https://s3-ap-northeast-1.amazonaws.com/image-recommender/test/"+name;
                  var url = 'data:image/png;base64,' + d.body;
                  return url;
              })
              .on("mouseover", tip.show)
              .on("mouseout", tip.hide);
              /*
              .text(function(d) { return d.vocab; })

              */

          /*
          objects.selectAll(".dot")
              .data(data)
              .enter()
              .append("circle")
              .classed("dot", true)
              .attr("r", 5)
              .attr("transform", transform)
              .style("fill", function(d) { return color(d[colorCat]); })
              .on("mouseover", tip.show)
           */

          /*
          var legend = svg.selectAll(".legend")
              .data(color.domain())
            .enter().append("g")
              .classed("legend", true)
              .attr("transform", function(d, i) { return "translate(0," + i * 20 + ")"; });

          legend.append("circle")
              .attr("r", 3.5)
              .attr("cx", width + 20)
              .attr("fill", color);

          legend.append("text")
              .attr("x", width + 26)
              .attr("dy", ".35em")
              .text(function(d) { return d; });
          */

          d3.select("input").on("click", change);

          function change() {
            xCat = "Carbs";
            xMax = d3.max(data, function(d) { return d.vector[0]; });
            xMin = d3.min(data, function(d) { return d.vector[0]; });

            zoomBeh.x(x.domain([xMin, xMax])).y(y.domain([yMin, yMax]));

            var svg = d3.select("#scatter").transition();

            svg.select(".x.axis").duration(750).call(xAxis).select(".label").text(xCat);

            objects.selectAll(".dot").transition().duration(1000).attr("transform", transform);
          }

        function zoom() {
          svg.select(".x.axis").call(xAxis);
          svg.select(".y.axis").call(yAxis);

          svg.selectAll(".dot")
              .attr("transform", transform);
        }

        function transform(d) {
          if(d.vector[0] && d.vector[1]){
            return "translate(" + x(d.vector[0]) + "," + y(d.vector[1]) + ")";
          }
        }

      },
      setRecipeFields: function(){
        this.recipeFields = {
          id: {
            label: this.$i18n.t("recipe.id"),
            sortable: false
          },
          "body.info.name": {
            label: this.$i18n.t("table.name"),
            sortable: true
          },
          "body.info.description": {
            label: this.$i18n.t("table.description"),
            sortable: false
          },
          updateTime: {
            label: this.$i18n.t("table.updateTime"),
            sortable: true,
          },
          createTime: {
            label: this.$i18n.t("table.createTime"),
            sortable: true,
          }
        };
      },
      setDataFields: function(){
        this.dataFields = {
          id: {
            label: this.$i18n.t("data.id"),
            sortable: false
          },
          name: {
            label: this.$i18n.t("table.name"),
            sortable: true,
          },
          description: {
            label: this.$i18n.t("table.description"),
            sortable: false,
          },
          updateTime: {
            label: this.$i18n.t("table.updateTime"),
            sortable: true,
          },
          createTime: {
            label: this.$i18n.t("table.createTime"),
            sortable: true,
          }
        };
      },
      setModelFields: function(){
        this.modelFields = {
          id: {
            label: this.$i18n.t("model.id"),
            sortable: false
          },
          name: {
            label: this.$i18n.t("table.name"),
            sortable: true,
          },
          description: {
            label: this.$i18n.t("table.description"),
            sortable: false,
          },
          recipe: {
            label: this.$i18n.t("model.recipe"),
            sortable: false,
          },
          data: {
            label: this.$i18n.t("model.data"),
            sortable: false,
          },
          updateTime: {
            label: this.$i18n.t("table.updateTime"),
            sortable: true,
          },
          createTime: {
            label: this.$i18n.t("table.createTime"),
            sortable: true,
          }
        };
      },
      getTargetIndex(targetList, targetId){
        for(let i=0; i< targetList.length; i++){
          if(targetList[i].id == targetId){
            return i;
          }
        }
      },
      getTarget(targetList, targetId){
        for(let i=0; i< targetList.length; i++){
          if(targetList[i].id == targetId){
            return targetList[i];
          }
        }
      },
    },
    watch: {
      selectedLanguage: function(newLocale, oldLocale){
        this.$i18n.locale = newLocale;
        setLocalSettings("language", newLocale)
      },
      imagesPerPage: function(newI, oldI){
        if(typeof　newI == "string"){
          this.imagesPerPage = parseInt(newI);
          setLocalSettings("imagesPerPage", newI)
        }
      },
      showAddRecipe: function(newShow, oldShow){
        if(newShow){
          this.$nextTick(()=>{
            this.buildGraph(this.newRecipe, "-new");
          });
        }
      },
      dimRedResult: function(newR, oldR){
        this.show2D(newR);
      }
    },

    computed: {
      recipeOptions: function(){
        const recipeOptions = []
        this.recipes.forEach((v) => {
          const text = (v.body.info && v.body.info.name)? v.body.info.name+" ("+v["id"]+")": v["id"]
          const option = {"value": v, "text": text};
          if(!v["body"]){
            option["disabled"]= true
          }
          recipeOptions.push(option);
        });
        return recipeOptions
      },
      learningDataOptions: function(){
        const options = []
        this.learningData.forEach((v) => {
          const option = {"value": v, "text": v["name"]+" ("+v["id"]+")"};
          if(v["nImages"].length != v["nLabels"].length){
            option["disabled"]= true
          }
          options.push(option);
        });
        return options
      },
      modelOptions: function(){
        const options = []
        this.models.forEach((v) => {
          const option = {"value": v, "text": v["name"]+" ("+v["id"]+")"};
          options.push(option);
        });
        return options
      },
    },
    created: function(){
      this.initRecipeLayers();
      this.initNewRecipe()
    },
    mounted: function (){
      this.setDataFields();
      this.setRecipeFields();
      this.setModelFields();
      this.setActivationOptions();
      this.setInferenceTypeOptions();
      this.initCharts(this.newModel);
      //this.show2D();

      this.languageOptions = [
        { value: "en", text: "English" },
        { value: "ja", text: "日本語" }
      ]

      var app = document.getElementById('app');
      console.log(app.style);
      console.log(app.style.visibility);
      app.style.visibility = "visible";


      if ('Notification' in window) {
        Notification.requestPermission()
        .then((permission) => {
          if (permission == 'granted') {
          } else if (permission == 'denied') {
          } else if (permission == 'default') {
          }
        });
      }



      this.ws.onopen = () => {
        console.log("ws open.");
        const recipesReq = {"action": "getRecipeList"};
        this.sendMessage(recipesReq);

        const dataReq = {"action": "getDataList"};
        this.sendMessage(dataReq);

        const modelReq = {"action": "getModelList"};
        this.sendMessage(modelReq);
      };
      this.ws.onclose = function(e){
        console.log("we close.");
        console.log(e);
      };

      this.ws.onmessage = (evt) => {
          const res  = JSON.parse(evt.data)
          console.log(res);
          if (res["action"] == "getDataList") {
            const dataList = res["list"];
            dataList.forEach(v=>{
              v.mode = "detail";
              v.bkup = Object.assign({},v);
              v.images = [];
              v.currentPage = 1;
              v.prevPage = 1;
            });
            this.learningData = dataList;
            console.log(this.learningData);
          }else if(res["action"] == "getData") {
            const index = this.getTargetIndex(this.learningData, res.dataId);
            const images = res.list;
            this.learningData[index].images = images;

          }else if(res["action"] == "getModelList") {
            const modelList = res["list"];
            modelList.forEach(v=>{
              v.mode = "detail";
              v.bkup = Object.assign({},v);
              this.initCharts(v, v.chartData);
            });
            this.models = modelList;
          }else if(res["action"] == "getRecipeList") {
            const recipes = res["list"];
            recipes.forEach(v=>{
              v.mode = "detail";
              v.bkup = {body:{info:{}}};
              v.bkup.body.info = Object.assign({},v.body.info);
              v.body.tappedLayer = {
                data: () => {
                  return {
                    name: ""
                  };
                },
                neighborhood: (selecter) => {
                  return [];
                }
              };
            });
            this.recipes = recipes;
          } else if (res["action"] == "addRecipe"){
            const recipesReq = {"action": "getRecipeList"};
            this.sendMessage(recipesReq);
            this.initNewRecipe()
            this.buildGraph(this.newRecipe, "-new");

          }else if (res["action"] == "finishLearning") {
            var n = new Notification(
                this.$i18n.t("message.finishLearning"),
                {
                  body: '',
                  icon: '',
                  tag: '',
                  data: {}
                }
              );
            const modelReq = {"action": "getModelList"};
            this.sendMessage(modelReq);
          }else if (res["action"] == "deleteModel") {
            const deleteId = this.getTargetIndex(this.models, res.modelId);
            this.$delete(this.models, deleteId);

          }else if (res["action"] == "deleteRecipe") {
            const deleteId = this.getTargetIndex(this.recipes, res.recipeId);
            this.$delete(this.recipes, deleteId);

          }else if (res["action"] == "deleteData") {
            const deleteId = this.getTargetIndex(this.learningData, res.dataId);
            this.$delete(this.learningData, deleteId);

          }else if (res["action"] == "updateData") {
            this.updateList(this.learningData, res.data, [{key: "images", value: []}]);

          }else if (res["action"] == "updateRecipe") {
            this.updateList(this.recipes, res.recipe);

          }else if (res["action"] == "updateModel") {
            this.updateList(this.models, res.model);

          }else if (res["action"] == "startUploading") {
            this.parseFile(this.uploadFile, 100000);

          }else if (res["action"] == "startUploadingInferenceZip") {
            this.parseFile(this.selectedInferenceFile, 100000);

          }else if (res["action"] == "inferenceSingleImage") {
            this.sendInferenceData();

          }else if (res["action"] == "finishClassfication") {
            this.classficationResult = res["list"];

          }else if (res["action"] == "finishVectorization") {
            this.vectorizationResult = res["list"];

          }else if (res["action"] == "finishDimRed") {
            this.dimRedResult = res["list"];

          }else if(res["action"] == "learning"){
            this.learningNumIter = res["nIter"]
            this.learningProgress = res["iter"]

          }else if(res["action"] == "evaluate_train"){
            this.addChartData(this.newModel.charts, "train_accuracy", res["iter"], res["accuracy"]);
            this.addChartData(this.newModel.charts, "train_loss", res["iter"], res["loss"]);

          }else if(res["action"] == "evaluate_test"){
            this.addChartData(this.newModel.charts, "test_accuracy", res["iter"], res["accuracy"]);
            this.addChartData(this.newModel.charts, "test_loss", res["iter"], res["loss"]);

          }else if(res["action"] == "uploaded"){
            this.progress = 0;
            this.newData.name = "";
            this.newData.description = "";
            this.uploadFile = null;
            const dataReq = {"action": "getDataList"};
            this.sendMessage(dataReq);

          } else if(res["action"] == "uploadingLearningData"){
            this.progress = res["loadedSize"]

          } else if(res["action"] == "uploadingInferenceZip"){
            console.log(res["loadedSize"])
            this.uploadInferenceZipProgress = res["loadedSize"]

          }else{
            console.log("Unknown action");
          }
      };
    }
  });
});

  Vue.component('line-chart', {
    extends: VueChartJs.Line,
    mixins: [VueChartJs.mixins.reactiveProp],
    props: ['chartData', 'options'],
    mounted () {
      this.renderChart(this.chartData, this.options)
    }
  });
};
